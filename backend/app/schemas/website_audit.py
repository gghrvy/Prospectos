from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebsiteAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    url: str | None = None

    http_status: int | None = None
    https_enabled: bool | None = None

    title: str | None = None
    meta_description: str | None = None

    page_count: int | None = None
    crawl_depth: int | None = None

    has_viewport: bool | None = None
    has_contact_form: bool | None = None
    has_email: bool | None = None
    has_phone: bool | None = None
    has_booking: bool | None = None
    has_faq: bool | None = None
    has_live_chat: bool | None = None
    has_ai_chatbot: bool | None = None
    has_whatsapp: bool | None = None
    has_social_links: bool | None = None
    discovered_email: str | None = None

    broken_link_count: int | None = None

    mobile_score: int | None = None
    design_score: int | None = None
    technical_score: int | None = None
    content_score: int | None = None
    conversion_score: int | None = None
    customer_experience_score: int | None = None

    website_quality_score: int | None = None
    ai_opportunity_score: int | None = None
    redesign_opportunity_score: int | None = None
    overall_opportunity_score: int | None = None

    quality_category: str | None = None
    opportunity_types: list[str] | None = None
    audit_summary: str | None = None
    opportunity_reasons: list[str] | None = None

    screenshot_desktop_path: str | None = None
    screenshot_mobile_path: str | None = None

    created_at: datetime
