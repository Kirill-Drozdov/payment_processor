from datetime import datetime
from typing import Optional
import uuid
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.datatypes import WebhookStatus
from core.db.postgres import Base


class OutboxEvent(Base):
    """Модель для гарантированной отправки webhook-уведомлений.
    """
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    payment_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[WebhookStatus] = mapped_column(
        Enum(WebhookStatus),
        nullable=False,
        default=WebhookStatus.PENDING,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_outbox_events_status_next_retry", "status", "next_retry_at"),
    )
