import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Contract(Base):
    """A generated document for a business that's said yes -- a Service
    Agreement, NDA, or Welcome Packet. Mirrors Outreach: new documents are
    created rather than overwriting old ones, so revisions stay visible as
    history. These are template starting points, not legal advice."""

    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "SERVICE_AGREEMENT" | "NDA" | "WELCOME_PACKET"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    studio_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    deposit_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Snapshot of the sender's details at generation time, same rationale
    # as Outreach.sender_* -- stays correct even if the sender is later
    # renamed or removed.
    sender_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("senders.id", ondelete="SET NULL"), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sender_portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
