# schemas/events.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.datatypes import PaymentStatus


class PaymentCreatedEvent(BaseModel):
    """Событие о совершении платежа."""
    payment_id: UUID
    status: PaymentStatus
    amount: str
    currency: str
    created_at: datetime
    webhook_url: str
