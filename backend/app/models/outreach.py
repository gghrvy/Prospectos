import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Outreach(Base):
    """A generated (and human-reviewable) outreach draft for a business.

    New drafts are created rather than overwriting old ones (see
    Regenerate Outreach in the UI), so past drafts remain visible.
    """

    __tablename__ = "outreach"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    angle: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "ollama" | "template"

    # Snapshot of the sender's details at generation time (not just a live
    # FK) so a draft's signature stays correct in history even if the
    # sender is later renamed or removed from the team.
    sender_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("senders.id", ondelete="SET NULL"), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sender_portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
