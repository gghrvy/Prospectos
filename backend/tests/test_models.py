import uuid

from app.models.business import Business
from app.models.enums import (
    LeadStatus,
    OpportunityType,
    PackageType,
    QualityCategory,
    WebsiteStatus,
)
from app.models.lead_status_history import LeadStatusHistory
from app.models.note import Note
from app.models.outreach import Outreach
from app.models.website_audit import WebsiteAudit


def test_create_business_with_defaults(db_session):
    business = Business(name="ABC Plumbing", category="Plumber", city="Houston")
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    assert business.id is not None
    assert uuid.UUID(business.id)
    assert business.website_status is None
    assert business.created_at is not None
    assert business.updated_at is not None


def test_website_audit_belongs_to_business_and_stores_score_reasons(db_session):
    business = Business(name="ABC Plumbing", category="Plumber")
    db_session.add(business)
    db_session.commit()

    audit = WebsiteAudit(
        business_id=business.id,
        url="https://example.com",
        quality_category=QualityCategory.POOR,
        opportunity_types=[OpportunityType.AI_CHATBOT.value, OpportunityType.BOOKING_AUTOMATION.value],
        opportunity_reasons=["No obvious AI chatbot was detected.", "No obvious booking option."],
        overall_opportunity_score=91,
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.business_id == business.id
    assert audit.opportunity_types == ["AI_CHATBOT", "BOOKING_AUTOMATION"]
    assert audit.overall_opportunity_score == 91


def test_outreach_and_lead_status_history_and_note_link_to_business(db_session):
    business = Business(name="ABC Plumbing", category="Plumber")
    db_session.add(business)
    db_session.commit()

    outreach = Outreach(business_id=business.id, angle="AI_CHATBOT", subject="Quick idea", body="Hi there...")
    history = LeadStatusHistory(business_id=business.id, status=LeadStatus.NEW.value)
    note = Note(business_id=business.id, content="Called, left voicemail.")

    db_session.add_all([outreach, history, note])
    db_session.commit()

    assert outreach.id is not None
    assert history.status == "NEW"
    assert note.content == "Called, left voicemail."


def test_website_status_enum_accepts_not_found(db_session):
    business = Business(name="No Website Co", category="Plumber", website_status=WebsiteStatus.NOT_FOUND.value)
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    assert business.website_status == "not_found"


def test_package_type_enum_values():
    assert {p.value for p in PackageType} == {"STANDARD", "FULL", "CUSTOM"}
