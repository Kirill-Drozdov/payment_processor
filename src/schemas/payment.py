import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.datatypes import Currency, PaymentStatus


class PaymentRequest(BaseModel):
    amount: Decimal
    currency: Currency
    description: str = Field(max_length=255)
    meta_data: dict = Field(default={})
    webhook_url: str = Field(max_length=500)


class PaymentResponse(BaseModel):
    id: UUID  # noqa
    status: PaymentStatus
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)
