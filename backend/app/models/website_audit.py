import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class WebsiteAudit(Base):
    """A single point-in-time audit of a business's website.

    A new row is created per audit run rather than overwriting the previous
    one, so audit history is preserved even when two developers re-audit the
    same business independently.
    """

    __tablename__ = "website_audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    https_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crawl_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)

    has_viewport: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_contact_form: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_email: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_phone: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    has_booking: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_faq: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_live_chat: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_ai_chatbot: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_whatsapp: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    has_social_links: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # The actual email address found on the site, if any -- never guessed,
    # only what was literally present on a crawled page.
    discovered_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    broken_link_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mobile_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    design_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_experience_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    website_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redesign_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quality_category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # List of OpportunityType.value strings. Stored as JSON (not a native
    # Postgres enum array) so this column works identically on SQLite
    # (local tests) and Postgres (shared Supabase).
    opportunity_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    audit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # List of human-readable reason strings behind the opportunity score.
    opportunity_reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    screenshot_desktop_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screenshot_mobile_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Python-side default (microsecond precision, deterministic ordering) —
    # see Business.created_at for why this isn't a server_default.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
