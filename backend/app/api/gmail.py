from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.config import get_settings
from app.database.session import get_db
from app.models.business import Business
from app.models.gmail_connection import GmailConnection
from app.models.lead_status_history import LeadStatusHistory
from app.models.outreach import Outreach
from app.models.outreach_activity import OutreachActivity
from app.models.outreach_batch import OutreachBatch
from app.services.gmail import access_token, authorization_url, exchange_code, send_message, validate_state

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    if get_settings().is_demo_mode:
        return {"connected": False, "email": None}
    connection = db.scalars(select(GmailConnection).order_by(GmailConnection.connected_at.desc()).limit(1)).first()
    return {"connected": bool(connection), "email": connection.email if connection else None}


@router.get("/connect")
def connect():
    return RedirectResponse(authorization_url(get_settings()))


@router.get("/callback")
def callback(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    if error or not code:
        return RedirectResponse("http://localhost:3000/prospects?gmail=cancelled")
    settings = get_settings()
    validate_state(state, settings)
    email, refresh_token = exchange_code(code, settings)
    encrypted = Fernet(settings.gmail_token_encryption_key.encode()).encrypt(refresh_token.encode()).decode()
    connection = db.scalars(select(GmailConnection).where(GmailConnection.email == email)).first()
    if connection:
        connection.refresh_token_encrypted = encrypted
        connection.connected_at = datetime.now(timezone.utc)
    else:
        db.add(GmailConnection(email=email, refresh_token_encrypted=encrypted))
    db.commit()
    return RedirectResponse("http://localhost:3000/prospects?gmail=connected")


@router.post("/outreach/{outreach_id}/send")
def send_outreach(outreach_id: str, db: Session = Depends(get_db)):
    outreach = db.get(Outreach, outreach_id)
    if not outreach:
        raise HTTPException(404, "Outreach draft not found")
    if outreach.sent_at:
        raise HTTPException(409, "This draft has already been sent.")
    if outreach.approval_status != "APPROVED":
        raise HTTPException(422, "Approve this draft before sending.")
    settings = get_settings()
    sent_today = db.scalar(select(func.count()).select_from(Outreach).where(
        Outreach.sent_at >= datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    )) or 0
    if sent_today >= settings.outreach_daily_send_limit:
        raise HTTPException(429, f"Daily send limit of {settings.outreach_daily_send_limit} reached.")
    business = db.get(Business, outreach.business_id)
    if not business or not business.email:
        raise HTTPException(422, "This prospect has no verified email address.")
    connection = db.scalars(select(GmailConnection).order_by(GmailConnection.connected_at.desc()).limit(1)).first()
    if not connection:
        raise HTTPException(422, "Connect Gmail before sending.")
    if not outreach.subject or not outreach.body:
        raise HTTPException(422, "This outreach draft is incomplete.")
    try:
        gmail_result = send_message(business.email, outreach.subject, outreach.body, connection.refresh_token_encrypted, settings)
        outreach.gmail_message_id = gmail_result["id"] if isinstance(gmail_result, dict) else gmail_result
        outreach.gmail_thread_id = gmail_result.get("threadId") if isinstance(gmail_result, dict) else None
    except HTTPException as exc:
        outreach.approval_status = "FAILED"
        db.add(OutreachActivity(outreach_id=outreach.id, business_id=business.id, action="SEND_FAILED", detail=exc.detail))
        db.commit()
        raise
    outreach.sent_at = datetime.now(timezone.utc)
    outreach.sent_to = business.email
    db.add(OutreachActivity(outreach_id=outreach.id, business_id=business.id, action="SENT", detail=f"Sent to {business.email} from {connection.email}"))
    db.commit()
    return {"sent": True, "to": business.email, "from": connection.email}


@router.post("/outreach/{outreach_id}/approve")
def approve_outreach(outreach_id: str, db: Session = Depends(get_db)):
    outreach = db.get(Outreach, outreach_id)
    if not outreach:
        raise HTTPException(404, "Outreach draft not found")
    if outreach.sent_at:
        raise HTTPException(409, "Sent drafts cannot be changed.")
    outreach.approval_status = "APPROVED"
    db.add(OutreachActivity(outreach_id=outreach.id, business_id=outreach.business_id, action="APPROVED", detail="Approved for batch sending"))
    db.commit()
    return {"approved": True}


@router.get("/activity")
def activity(db: Session = Depends(get_db)):
    rows = db.scalars(select(OutreachActivity).order_by(OutreachActivity.created_at.desc()).limit(50)).all()
    sent_today = sum(1 for row in rows if row.action == "SENT" and row.created_at.date() == datetime.now(timezone.utc).date())
    return {"sent_today": sent_today, "daily_limit": get_settings().outreach_daily_send_limit, "items": [
        {"id": row.id, "outreach_id": row.outreach_id, "business_id": row.business_id, "action": row.action, "detail": row.detail, "created_at": row.created_at}
        for row in rows
    ]}


@router.get("/report")
def report(db: Session = Depends(get_db)):
    counts = {action: db.scalar(select(func.count()).select_from(OutreachActivity).where(OutreachActivity.action == action)) or 0
              for action in ("SENT", "SEND_FAILED", "REPLIED", "APPROVED", "QUEUED")}
    pipeline = {status: db.scalar(select(func.count()).select_from(OutreachActivity).where(OutreachActivity.action == status)) or 0 for status in ("POSITIVE_REPLY", "MEETING", "PROPOSAL", "WON")}
    return {"sent": counts["SENT"], "failed": counts["SEND_FAILED"], "replied": counts["REPLIED"], "approved": counts["APPROVED"], "queued": counts["QUEUED"], **pipeline}


@router.post("/sync-replies")
def sync_replies(db: Session = Depends(get_db)):
    connection = db.scalars(select(GmailConnection).order_by(GmailConnection.connected_at.desc()).limit(1)).first()
    if not connection:
        raise HTTPException(422, "Connect Gmail before syncing replies.")
    import httpx
    token = access_token(connection.refresh_token_encrypted, get_settings())
    response = httpx.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", params={"q": "in:inbox newer_than:30d", "maxResults": 100}, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if response.is_error:
        raise HTTPException(502, "Gmail could not retrieve replies. Reconnect Gmail with the read permission.")
    sent = db.scalars(select(Outreach).where(Outreach.sent_at.is_not(None))).all()
    by_recipient: dict[str, list[Outreach]] = {}
    by_thread = {item.gmail_thread_id: item for item in sent if item.gmail_thread_id}
    by_message = {item.gmail_message_id: item for item in sent if item.gmail_message_id}
    for outreach in sent:
        if outreach.sent_to:
            by_recipient.setdefault(outreach.sent_to.lower(), []).append(outreach)
    matched = 0
    for item in response.json().get("messages", []):
        message = httpx.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", params={"format": "metadata", "metadataHeaders": ["From", "In-Reply-To", "References"]}, headers={"Authorization": f"Bearer {token}"}, timeout=20)
        headers = {h["name"].lower(): h["value"] for h in message.json().get("payload", {}).get("headers", [])} if message.is_success else {}
        sender = headers.get("from", "").lower()
        if db.scalars(select(OutreachActivity).where(OutreachActivity.external_id == item["id"])).first():
            continue
        references = f"{headers.get('in-reply-to', '')} {headers.get('references', '')}"
        outreach = by_thread.get(item.get("threadId"))
        if not outreach:
            outreach = next((candidate for message_id, candidate in by_message.items() if message_id and message_id in references), None)
        candidates = [candidate for email, values in by_recipient.items() if email in sender for candidate in values]
        if not outreach and len(candidates) == 1:
            outreach = candidates[0]
        if outreach:
            db.add(OutreachActivity(outreach_id=outreach.id, business_id=outreach.business_id, action="REPLIED", detail=f"Reply detected from {sender}", external_id=item["id"]))
            outreach.replied_at = datetime.now(timezone.utc)
            outreach.approval_status = "REPLIED"
            db.add(LeadStatusHistory(business_id=outreach.business_id, status="REPLIED", note="Confirmed Gmail reply"))
            matched += 1
    db.commit()
    return {"replies_detected": matched}


@router.get("/approval-queue")
def approval_queue(db: Session = Depends(get_db)):
    # Regenerating outreach deliberately retains old drafts on the prospect
    # record. The workspace, however, should offer only the current draft for
    # each prospect; otherwise one prospect can appear multiple times and be
    # queued more than once. Rank every draft first, then filter the current
    # one for actionable queue conditions.
    latest_drafts = (
        select(
            Outreach.id.label("outreach_id"),
            func.row_number().over(
                partition_by=Outreach.business_id,
                order_by=(Outreach.created_at.desc(), Outreach.id.desc()),
            ).label("position"),
        )
        .subquery()
    )
    rows = db.execute(
        select(Outreach, Business)
        .join(Business, Business.id == Outreach.business_id)
        .join(latest_drafts, latest_drafts.c.outreach_id == Outreach.id)
        .where(
            latest_drafts.c.position == 1,
            Outreach.sent_at.is_(None),
            Outreach.replied_at.is_(None),
            Outreach.batch_id.is_(None),
            Business.email.is_not(None),
        )
        .order_by(Outreach.created_at.desc())
        .limit(100)
    ).all()
    return {"items": [{
        "outreach_id": outreach.id, "business_id": business.id, "business_name": business.name,
        "email": business.email, "subject": outreach.subject, "approval_status": outreach.approval_status,
        "created_at": outreach.created_at,
    } for outreach, business in rows]}


@router.post("/batches")
def create_batch(payload: dict, db: Session = Depends(get_db)):
    name = str(payload.get("name") or "").strip()
    outreach_ids = payload.get("outreach_ids") or []
    if not name or not outreach_ids:
        raise HTTPException(422, "A batch name and at least one approved draft are required.")
    drafts = db.scalars(select(Outreach).where(Outreach.id.in_(outreach_ids), Outreach.sent_at.is_(None), Outreach.replied_at.is_(None), Outreach.approval_status == "APPROVED")).all()
    if len(drafts) != len(set(outreach_ids)):
        raise HTTPException(422, "Every batch draft must be approved and unsent.")
    batch = OutreachBatch(name=name, status="ACTIVE", timezone=str(payload.get("timezone") or "UTC"))
    db.add(batch)
    db.flush()
    for draft in drafts:
        draft.batch_id = batch.id
        db.add(OutreachActivity(outreach_id=draft.id, business_id=draft.business_id, action="QUEUED", detail=f"Queued in batch: {name}"))
    db.commit()
    return {"id": batch.id, "name": batch.name, "count": len(drafts), "status": batch.status}


@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    batches = db.scalars(select(OutreachBatch).order_by(OutreachBatch.created_at.desc())).all()
    return [{"id": batch.id, "name": batch.name, "status": batch.status, "created_at": batch.created_at,
             "count": db.scalar(select(func.count()).select_from(Outreach).where(Outreach.batch_id == batch.id)), "timezone": batch.timezone} for batch in batches]


@router.post("/batches/{batch_id}/{action}")
def control_batch(batch_id: str, action: str, db: Session = Depends(get_db)):
    if action not in {"pause", "resume", "cancel"}:
        raise HTTPException(404, "Unknown batch action")
    batch = db.get(OutreachBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if action == "pause": batch.status = "PAUSED"
    elif action == "resume": batch.status = "ACTIVE"
    else:
        batch.status = "CANCELLED"
        for draft in db.scalars(select(Outreach).where(Outreach.batch_id == batch.id, Outreach.sent_at.is_(None))).all():
            draft.batch_id = None
    db.commit()
    return {"id": batch.id, "status": batch.status}


@router.post("/batches/{batch_id}/dispatch")
def dispatch_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(OutreachBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    settings = get_settings()
    try:
        local_now = datetime.now(ZoneInfo(batch.timezone))
    except ZoneInfoNotFoundError:
        raise HTTPException(422, "Batch has an invalid IANA timezone.")
    hour = local_now.hour
    if hour < batch.send_hour_start or hour >= batch.send_hour_end:
        raise HTTPException(422, f"This batch sends only between {batch.send_hour_start}:00 and {batch.send_hour_end}:00 local server time.")
    start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    already_sent = db.scalar(select(func.count()).select_from(Outreach).where(Outreach.sent_at >= start)) or 0
    remaining = max(0, settings.outreach_daily_send_limit - already_sent)
    if not remaining:
        raise HTTPException(429, f"Daily send limit of {settings.outreach_daily_send_limit} reached.")
    hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    sent_this_hour = db.scalar(select(func.count()).select_from(Outreach).where(Outreach.sent_at >= hour_start)) or 0
    remaining = min(remaining, max(0, settings.outreach_hourly_send_limit - sent_this_hour))
    if not remaining:
        raise HTTPException(429, f"Hourly send limit of {settings.outreach_hourly_send_limit} reached.")
    drafts = db.scalars(select(Outreach).where(
        Outreach.batch_id == batch.id, Outreach.approval_status == "APPROVED", Outreach.sent_at.is_(None), Outreach.replied_at.is_(None), Outreach.followup_paused.is_(False),
    ).order_by(Outreach.created_at).limit(remaining)).all()
    sent, failed = 0, 0
    for draft in drafts:
        try:
            send_outreach(draft.id, db)
            sent += 1
        except HTTPException:
            failed += 1
    pending = db.scalar(select(func.count()).select_from(Outreach).where(Outreach.batch_id == batch.id, Outreach.approval_status == "APPROVED", Outreach.sent_at.is_(None), Outreach.replied_at.is_(None))) or 0
    batch.status = "COMPLETE" if pending == 0 else "ACTIVE"
    db.commit()
    return {"sent": sent, "failed": failed, "remaining_daily_capacity": max(0, remaining - sent)}
