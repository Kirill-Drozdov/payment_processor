import datetime as dt
from typing import Sequence
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.datatypes import WebhookStatus
from core.db.models import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_event(
        self,
        payment_id: UUID,
        webhook_url: str,
        payload: dict,
    ) -> OutboxEvent:
        """Создаёт запись в outbox."""
        event = OutboxEvent(
            payment_id=payment_id,
            webhook_url=webhook_url,
            payload=payload,
            status="pending",
            next_retry_at=dt.datetime.now(dt.timezone.utc),
        )
        self._session.add(event)
        await self._session.commit()
        return event

    async def get_pending_events(
        self,
        limit: int = 100,
    ) -> Sequence[OutboxEvent]:
        """Возвращает события, готовые к отправке."""
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .where(
                OutboxEvent.next_retry_at <= dt.datetime.now(dt.timezone.utc)
            )
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processing(self, event_id: UUID) -> None:
        """Переводит событие в статус processing (перед отправкой)."""
        await self._session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status="processing",
                updated_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await self._session.commit()

    async def mark_completed_or_failed(
        self,
        event_id: UUID,
        status: WebhookStatus,
    ) -> None:
        """Помечает событие completed после успешной отправки."""
        # Для простоты удаляем, можно и помечать completed
        await self._session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=status.value,
                updated_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await self._session.commit()

    async def mark_pending(
        self,
        event_id: UUID,
        next_retry_at: dt.datetime,
        retry_count: int,
    ) -> None:
        """Обновляет событие после неудачной отправки."""
        await self._session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status="pending",
                retry_count=retry_count,
                next_retry_at=next_retry_at,
                updated_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await self._session.commit()
