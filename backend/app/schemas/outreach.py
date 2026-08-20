from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OutreachGenerateRequest(BaseModel):
    """Optional angle override; if omitted the outreach service picks the
    strongest angle from the latest audit's opportunity_types. Optional
    sender: whichever teammate is picked gets their name/title/contact
    appended as the draft's signature."""

    angle: str | None = None
    sender_id: str | None = None


class OutreachRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    angle: str | None = None
    subject: str | None = None
    body: str | None = None
    generated_by: str | None = None
    sender_id: str | None = None
    sender_name: str | None = None
    sender_title: str | None = None
    sender_email: str | None = None
    sender_phone: str | None = None
    sender_portfolio_url: str | None = None
    created_at: datetime
