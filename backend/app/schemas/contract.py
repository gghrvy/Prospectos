from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ContractType = Literal["SERVICE_AGREEMENT", "NDA", "WELCOME_PACKET"]


class ContractGenerateRequest(BaseModel):
    contract_type: ContractType
    sender_id: str | None = None
    studio_name: str | None = None
    project_description: str | None = None
    price_amount: float | None = None
    currency: str = "USD"
    deposit_percent: int = 50


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    contract_type: str
    content: str
    studio_name: str | None = None
    project_description: str | None = None
    price_amount: float | None = None
    currency: str | None = None
    deposit_percent: int | None = None
    sender_id: str | None = None
    sender_name: str | None = None
    sender_title: str | None = None
    sender_email: str | None = None
    sender_phone: str | None = None
    sender_portfolio_url: str | None = None
    created_at: datetime
