import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.config import get_settings
from app.database.session import get_db
from app.models.business import Business
from app.models.contract import Contract
from app.models.lead_status_history import LeadStatusHistory
from app.models.note import Note
from app.models.outreach import Outreach
from app.models.sender import Sender
from app.models.website_audit import WebsiteAudit
from app.schemas.business import BusinessCreate, BusinessListItem, BusinessRead, BusinessUpdate
from app.schemas.business_detail import BusinessDetail
from app.schemas.common import PaginatedResponse
from app.schemas.contract import ContractGenerateRequest, ContractRead
from app.schemas.discovery import GeocodeRequest, GeocodeResult, OSMSearchRequest, SaveBusinessesRequest
from app.schemas.lead_status_history import LeadStatusChange, LeadStatusHistoryRead
from app.schemas.note import NoteCreate, NoteRead
from app.schemas.outreach import OutreachGenerateRequest, OutreachRead
from app.schemas.website_audit import WebsiteAuditRead
from app.services.audit_pipeline import run_audit
from app.services.discovery import (
    CSVProvider,
    GeoapifyProvider,
    OpenStreetMapProvider,
    deduplicate_businesses,
)
from app.services.discovery.geoapify import GEOAPIFY_KNOWN_CATEGORIES
from app.services.discovery.openstreetmap import KNOWN_CATEGORIES
from app.services.contracts import render_nda, render_service_agreement, render_welcome_packet
from app.services.outreach.generator import generate_outreach_draft

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

_SORTABLE_FIELDS = {"created_at", "name", "city", "category", "rating", "review_count"}
_CSV_EXPORT_FIELDS = [
    "id", "name", "category", "address", "city", "state", "country",
    "phone", "email", "website", "source", "rating", "review_count",
    "website_status", "created_at",
]


@router.get("", response_model=PaginatedResponse[BusinessListItem])
def list_businesses(
    db: Session = Depends(get_db),
    category: str | None = None,
    city: str | None = None,
    website_status: str | None = None,
    search: str | None = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if sort_by not in _SORTABLE_FIELDS:
        raise HTTPException(400, f"sort_by must be one of {sorted(_SORTABLE_FIELDS)}")

    query = select(Business)
    if category:
        query = query.where(Business.category == category)
    if city:
        query = query.where(Business.city == city)
    if website_status:
        query = query.where(Business.website_status == website_status)
    if search:
        query = query.where(Business.name.ilike(f"%{search}%"))

    total = db.scalar(select(sa_func.count()).select_from(query.subquery())) or 0

    sort_column = getattr(Business, sort_by)
    query = query.order_by(sort_column.desc() if sort_dir == "desc" else sort_column.asc())
    query = query.limit(limit).offset(offset)

    businesses = list(db.scalars(query).all())
    business_ids = [b.id for b in businesses]

    latest_audit_by_business: dict[str, WebsiteAudit] = {}
    latest_status_by_business: dict[str, str] = {}

    if business_ids:
        # ORDER BY business_id, created_at DESC groups each business's rows
        # together with the newest first — first-seen-wins below then picks
        # the latest row per business without a window function.
        audit_rows = db.execute(
            select(WebsiteAudit)
            .where(WebsiteAudit.business_id.in_(business_ids))
            .order_by(WebsiteAudit.business_id, WebsiteAudit.created_at.desc())
        ).scalars()
        for audit in audit_rows:
            latest_audit_by_business.setdefault(audit.business_id, audit)

        status_rows = db.execute(
            select(LeadStatusHistory.business_id, LeadStatusHistory.status)
            .where(LeadStatusHistory.business_id.in_(business_ids))
            .order_by(LeadStatusHistory.business_id, LeadStatusHistory.created_at.desc())
        ).all()
        for business_id, status in status_rows:
            latest_status_by_business.setdefault(business_id, status)

    items = []
    for business in businesses:
        latest_audit = latest_audit_by_business.get(business.id)
        items.append(
            BusinessListItem(
                **BusinessRead.model_validate(business).model_dump(),
                latest_opportunity_score=latest_audit.overall_opportunity_score if latest_audit else None,
                latest_quality_category=latest_audit.quality_category if latest_audit else None,
                current_status=latest_status_by_business.get(business.id),
            )
        )

    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=BusinessRead, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("source"):
        data["source"] = "manual"
    business = Business(**data)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/export-csv")
def export_businesses_csv(db: Session = Depends(get_db)):
    businesses = db.scalars(select(Business).order_by(Business.created_at.desc())).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_EXPORT_FIELDS)
    writer.writeheader()
    for business in businesses:
        writer.writerow({field: getattr(business, field) for field in _CSV_EXPORT_FIELDS})

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=prospectos_export.csv"},
    )


@router.post("/import-csv")
async def import_businesses_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    content = raw.decode("utf-8-sig")

    candidates = CSVProvider().discover(csv_text=content)
    existing = db.scalars(select(Business)).all()
    unique = deduplicate_businesses(list(existing), candidates)

    created: list[Business] = []
    for candidate in unique:
        business = Business(**candidate.model_dump())
        db.add(business)
        created.append(business)
    db.commit()
    for business in created:
        db.refresh(business)

    return {
        "total_rows": len(candidates),
        "imported": len(created),
        "skipped_duplicates": len(candidates) - len(unique),
        "businesses": [BusinessRead.model_validate(b) for b in created],
    }


@router.get("/search/categories")
def list_known_categories():
    """Category terms known to map onto a precise tag on at least one
    provider (real, API-backed suggestions rather than a freeform box that
    silently returns nothing for unrecognized terms) — the union of OSM's
    curated tag map and Geoapify's curated category map, since either
    provider might end up answering a given search. Any other term still
    works via a broader fallback (OSM regex search, or Geoapify's
    taxonomy-substring match) — this just tells the frontend what's a safe
    bet. A comma-separated list (e.g. "cafe, restaurant") also works and
    searches all of them in one request."""
    return {"categories": sorted(set(KNOWN_CATEGORIES) | set(GEOAPIFY_KNOWN_CATEGORIES))}


@router.post("/search/geocode", response_model=GeocodeResult)
def geocode_place(payload: GeocodeRequest):
    """Resolves a typed place name to coordinates — used to validate a city
    before running the full search, and to recenter the map-search mode.
    Falls back to Geoapify's geocoder (if configured) on the same principle
    as the business search itself: independent infrastructure, not just a
    retry of the same service."""
    try:
        return OpenStreetMapProvider().geocode(payload.place)
    except ValueError as osm_error:
        settings = get_settings()
        if not settings.geoapify_api_key:
            raise HTTPException(400, str(osm_error)) from osm_error
        try:
            return GeoapifyProvider(api_key=settings.geoapify_api_key).geocode(payload.place)
        except ValueError as geoapify_error:
            raise HTTPException(400, str(geoapify_error)) from geoapify_error


@router.post("/search")
def search_businesses(payload: OSMSearchRequest, db: Session = Depends(get_db)):
    search_kwargs = dict(
        category=payload.category,
        city=payload.city,
        country=payload.country,
        radius_km=payload.radius_km,
        limit=payload.limit,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    try:
        candidates = OpenStreetMapProvider().discover(**search_kwargs)
    except ValueError as osm_error:
        # OSM (Overpass) is the primary source and tried first always. If
        # it's down -- a real, observed failure mode, not hypothetical --
        # and a free-tier Geoapify key is configured, fall back to it
        # automatically rather than making the user retry manually or give
        # up on automated discovery entirely.
        settings = get_settings()
        if not settings.geoapify_api_key:
            raise HTTPException(400, str(osm_error)) from osm_error
        try:
            candidates = GeoapifyProvider(api_key=settings.geoapify_api_key).discover(**search_kwargs)
        except ValueError as geoapify_error:
            raise HTTPException(
                400,
                f"OpenStreetMap failed ({osm_error}) and the Geoapify fallback also failed ({geoapify_error}).",
            ) from geoapify_error

    existing = db.scalars(select(Business)).all()
    unique = deduplicate_businesses(list(existing), candidates)

    if not payload.save:
        return unique

    return _persist_candidates(db, unique)


def _resolve_sender_snapshot(db: Session, sender_id: str | None) -> dict:
    """Looks up a Sender and returns the denormalized snapshot fields
    stored on Outreach/Contract rows -- shared by both generation
    endpoints so a sender resolves identically (and 404s identically)
    either way."""
    if not sender_id:
        return {}
    sender = db.get(Sender, sender_id)
    if not sender:
        raise HTTPException(404, "Sender not found")
    return {
        "sender_id": sender.id,
        "sender_name": sender.name,
        "sender_title": sender.title,
        "sender_email": sender.email,
        "sender_phone": sender.phone,
        "sender_portfolio_url": sender.portfolio_url,
    }


def _persist_candidates(db: Session, candidates: list) -> list[BusinessRead]:
    created: list[Business] = []
    for candidate in candidates:
        business = Business(**candidate.model_dump())
        db.add(business)
        created.append(business)
    db.commit()
    for business in created:
        db.refresh(business)
    return [BusinessRead.model_validate(b) for b in created]


@router.post("/save", response_model=list[BusinessRead], status_code=201)
def save_businesses(payload: SaveBusinessesRequest, db: Session = Depends(get_db)):
    """Saves specific already-fetched search results (e.g. rows checked in
    Discover) directly -- no re-search, so picking a few prospects out of a
    batch doesn't cost another discovery API call. Still deduplicates
    against what's already saved and within the selected batch itself."""
    existing = db.scalars(select(Business)).all()
    unique = deduplicate_businesses(list(existing), payload.businesses)
    return _persist_candidates(db, unique)


@router.get("/{business_id}", response_model=BusinessDetail)
def get_business(business_id: str, db: Session = Depends(get_db)):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")

    audits = db.scalars(
        select(WebsiteAudit)
        .where(WebsiteAudit.business_id == business_id)
        .order_by(WebsiteAudit.created_at.desc())
    ).all()
    outreach_drafts = db.scalars(
        select(Outreach).where(Outreach.business_id == business_id).order_by(Outreach.created_at.desc())
    ).all()
    contracts = db.scalars(
        select(Contract).where(Contract.business_id == business_id).order_by(Contract.created_at.desc())
    ).all()
    status_history = db.scalars(
        select(LeadStatusHistory)
        .where(LeadStatusHistory.business_id == business_id)
        .order_by(LeadStatusHistory.created_at.desc())
    ).all()
    notes = db.scalars(
        select(Note).where(Note.business_id == business_id).order_by(Note.created_at.desc())
    ).all()

    return BusinessDetail(
        **BusinessRead.model_validate(business).model_dump(),
        current_status=status_history[0].status if status_history else None,
        latest_audit=audits[0] if audits else None,
        audits=list(audits),
        outreach_drafts=list(outreach_drafts),
        contracts=list(contracts),
        status_history=list(status_history),
        notes=list(notes),
    )


@router.patch("/{business_id}", response_model=BusinessRead)
def update_business(business_id: str, payload: BusinessUpdate, db: Session = Depends(get_db)):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, field, value)
    db.commit()
    db.refresh(business)
    return business


@router.delete("/{business_id}", status_code=204)
def delete_business(business_id: str, db: Session = Depends(get_db)):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    db.delete(business)
    db.commit()


@router.post("/{business_id}/audit", response_model=WebsiteAuditRead, status_code=201)
def run_business_audit(business_id: str, db: Session = Depends(get_db)):
    """Runs discovery-of-truth (crawl -> analyze -> score) for one business
    and inserts a new WebsiteAudit row — audits are never overwritten, so
    both developers can see the full history via the shared DB (spec
    section 36)."""
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")

    audit_data = run_audit(business)
    audit = WebsiteAudit(business_id=business_id, **audit_data)
    db.add(audit)

    business.website_status = (
        "not_found" if not business.website else ("exists" if audit_data.get("http_status") else "unreachable")
    )

    # A real email found on the crawl fills in a blank contact field --
    # never overwrites one that's already there (could be more accurate
    # than what the crawler found, e.g. a direct line someone entered by hand).
    discovered_email = audit_data.get("discovered_email")
    if discovered_email and not business.email:
        business.email = discovered_email

    db.commit()
    db.refresh(audit)
    return audit


@router.post("/{business_id}/outreach", response_model=OutreachRead, status_code=201)
def generate_business_outreach(business_id: str, payload: OutreachGenerateRequest, db: Session = Depends(get_db)):
    """Generates one outreach draft from the business's latest audit
    findings and inserts a new Outreach row — never overwrites a prior
    draft, so "Regenerate Outreach" keeps full history."""
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")

    latest_audit = db.scalars(
        select(WebsiteAudit)
        .where(WebsiteAudit.business_id == business_id)
        .order_by(WebsiteAudit.created_at.desc())
        .limit(1)
    ).first()

    opportunity_types = (latest_audit.opportunity_types if latest_audit else None) or ["NO_WEBSITE"]
    opportunity_reasons = (latest_audit.opportunity_reasons if latest_audit else None) or [
        "Website not found from available sources."
    ]

    sender_snapshot = _resolve_sender_snapshot(db, payload.sender_id)

    draft = generate_outreach_draft(
        business_name=business.name,
        category=business.category,
        opportunity_types=opportunity_types,
        opportunity_reasons=opportunity_reasons,
        angle=payload.angle,
        sender={
            "name": sender_snapshot.get("sender_name"),
            "title": sender_snapshot.get("sender_title"),
            "email": sender_snapshot.get("sender_email"),
            "phone": sender_snapshot.get("sender_phone"),
            "portfolio_url": sender_snapshot.get("sender_portfolio_url"),
        }
        if sender_snapshot
        else None,
        social_proof={"rating": business.rating, "review_count": business.review_count},
    )

    outreach = Outreach(business_id=business_id, **draft, **sender_snapshot)
    db.add(outreach)
    db.commit()
    db.refresh(outreach)
    return outreach


_CONTRACT_RENDERERS = {
    "SERVICE_AGREEMENT": lambda business, studio_name, snap, payload: render_service_agreement(
        business_name=business.name,
        studio_name=studio_name,
        sender_name=snap.get("sender_name"),
        sender_title=snap.get("sender_title"),
        sender_email=snap.get("sender_email"),
        project_description=payload.project_description,
        price_amount=payload.price_amount,
        currency=payload.currency,
        deposit_percent=payload.deposit_percent,
    ),
    "NDA": lambda business, studio_name, snap, payload: render_nda(
        business_name=business.name,
        studio_name=studio_name,
        sender_name=snap.get("sender_name"),
    ),
    "WELCOME_PACKET": lambda business, studio_name, snap, payload: render_welcome_packet(
        business_name=business.name,
        studio_name=studio_name,
        sender_name=snap.get("sender_name"),
        sender_title=snap.get("sender_title"),
        sender_email=snap.get("sender_email"),
        sender_phone=snap.get("sender_phone"),
        sender_portfolio_url=snap.get("sender_portfolio_url"),
        project_description=payload.project_description,
    ),
}


@router.post("/{business_id}/contract", response_model=ContractRead, status_code=201)
def generate_business_contract(business_id: str, payload: ContractGenerateRequest, db: Session = Depends(get_db)):
    """Generates a Service Agreement, NDA, or Welcome Packet for a business
    that's said yes -- template starting points, not legal advice (spec:
    review with a real legal plugin/lawyer before relying on these for
    real money). Never overwrites a prior document, so revisions stay
    visible as history, same as Outreach."""
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")

    sender_snapshot = _resolve_sender_snapshot(db, payload.sender_id)
    studio_name = payload.studio_name or "our studio"

    content = _CONTRACT_RENDERERS[payload.contract_type](business, studio_name, sender_snapshot, payload)

    contract = Contract(
        business_id=business_id,
        contract_type=payload.contract_type,
        content=content,
        studio_name=studio_name,
        project_description=payload.project_description,
        price_amount=payload.price_amount,
        currency=payload.currency,
        deposit_percent=payload.deposit_percent,
        **sender_snapshot,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.post("/{business_id}/notes", response_model=NoteRead, status_code=201)
def add_note(business_id: str, payload: NoteCreate, db: Session = Depends(get_db)):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    note = Note(business_id=business_id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.post("/{business_id}/status", response_model=LeadStatusHistoryRead, status_code=201)
def change_status(business_id: str, payload: LeadStatusChange, db: Session = Depends(get_db)):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    history = LeadStatusHistory(business_id=business_id, **payload.model_dump())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
