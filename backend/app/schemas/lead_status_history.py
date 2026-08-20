from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadStatusChange(BaseModel):
    status: str
    note: str | None = None
    changed_by: str | None = None


class LeadStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    status: str
    note: str | None = None
    changed_by: str | None = None
    created_at: datetime
