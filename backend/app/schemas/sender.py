from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SenderCreate(BaseModel):
    name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    portfolio_url: str | None = None


class SenderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    portfolio_url: str | None = None
    created_at: datetime
