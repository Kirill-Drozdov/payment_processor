# consumer/outbox_worker.py
import asyncio
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from consumer.webhook_sender import send_webhook
from core.config import settings
from core.db.postgres import async_session
from repository.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Фоновый воркер, который отправляет ожидающие webhook-уведомления."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Outbox worker started")
        while self._running:
            try:
                await self._process_pending_events()
            except Exception as e:
                logger.exception(f"Outbox worker error: {e}")
            await asyncio.sleep(settings.outbox_poll_interval)

    async def stop(self):
        self._running = False

    async def _process_pending_events(self):
        async with self.session_factory() as session:
            repo = OutboxRepository(session)
            events = await repo.get_pending_events(limit=50)

            for event in events:
                # Помечаем как processing
                await repo.mark_processing(event.id)
                await session.commit()

                # Отправляем webhook
                success = await send_webhook(
                    url=event.webhook_url,
                    payload=event.payload,
                    timeout=settings.webhook_timeout,
                )

                if success:
                    await repo.mark_completed(event.id)
                else:
                    # Экспоненциальная задержка
                    new_retry_count = event.retry_count + 1
                    if new_retry_count >= settings.max_webhook_retries:
                        # Превышено число попыток – помечаем как failed (можно отправить в DLQ или просто логировать)
                        logger.error(
                            f"Webhook failed after {new_retry_count} attempts: {event.id}")
                        # Можно удалить или пометить failed
                        # удаляем, чтобы не засорять
                        await repo.mark_completed(event.id)
                    else:
                        delay = settings.base_retry_delay * \
                            (2 ** (new_retry_count - 1))
                        next_retry = datetime.utcnow() + timedelta(seconds=delay)
                        await repo.mark_failed(event.id, next_retry, new_retry_count)

                await session.commit()
