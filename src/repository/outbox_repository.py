from uuid import UUID
from datetime import datetime
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

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
        """Создаёт запись в outbox (в рамках текущей транзакции)."""
        event = OutboxEvent(
            payment_id=payment_id,
            webhook_url=webhook_url,
            payload=payload,
            status="pending",
            next_retry_at=datetime.utcnow(),
        )
        self._session.add(event)
        return event

    async def get_pending_events(
        self,
        limit: int = 100,
    ) -> Sequence[OutboxEvent]:
        """Возвращает события, готовые к отправке."""
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .where(OutboxEvent.next_retry_at <= datetime.utcnow())
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
            .values(status="processing", updated_at=datetime.utcnow())
        )

    async def mark_completed(self, event_id: UUID) -> None:
        """Удаляет событие после успешной отправки (либо помечает completed)."""
        # Для простоты удаляем, можно и помечать completed
        await self._session.delete(
            await self._session.get(OutboxEvent, event_id)
        )

    async def mark_failed(
        self,
        event_id: UUID,
        next_retry_at: datetime,
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
                updated_at=datetime.utcnow(),
            )
        )
