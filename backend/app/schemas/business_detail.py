from app.schemas.business import BusinessRead
from app.schemas.contract import ContractRead
from app.schemas.lead_status_history import LeadStatusHistoryRead
from app.schemas.note import NoteRead
from app.schemas.outreach import OutreachRead
from app.schemas.website_audit import WebsiteAuditRead


class BusinessDetail(BusinessRead):
    """Composite view for the prospect detail page: the business plus all
    of its related records, newest first."""

    current_status: str | None = None
    latest_audit: WebsiteAuditRead | None = None
    audits: list[WebsiteAuditRead] = []
    outreach_drafts: list[OutreachRead] = []
    contracts: list[ContractRead] = []
    status_history: list[LeadStatusHistoryRead] = []
    notes: list[NoteRead] = []
