import asyncio
from datetime import datetime, timedelta, timezone
import logging

from consumer.webhook_sender import send_webhook
from core.config import settings
from core.datatypes import WebhookStatus
from core.db.models.outbox_event import OutboxEvent
from repository.outbox_repository import OutboxRepository


class OutboxWorker:
    """Фоновый воркер, который отправляет ожидающие webhook-уведомления."""
    _logger = logging.getLogger(__name__)

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._running = False

    async def start(self):
        self._running = True
        self._logger.info("Outbox worker started")
        while self._running:
            try:
                await self._process_pending_events()
            except Exception as e:
                self._logger.exception(f"Outbox worker error: {e}")
            await asyncio.sleep(settings.outbox_poll_interval)

    async def stop(self):
        self._running = False

    async def _process_event(
        self,
        event: OutboxEvent,
    ) -> None:
        async with self.session_factory() as session:
            try:
                _outbox_repository = OutboxRepository(session)

                # Помечаем как processing.
                await _outbox_repository.mark_processing(event.id)

                # Отправляем webhook.
                success = await send_webhook(
                    url=event.webhook_url,
                    payload=event.payload,
                    timeout=settings.webhook_timeout,
                )

                if success:
                    await _outbox_repository.mark_completed_or_failed(
                        event_id=event.id,
                        status=WebhookStatus.COMPLETED,
                    )
                else:
                    # Экспоненциальная задержка.
                    new_retry_count = event.retry_count + 1
                    if new_retry_count >= settings.max_webhook_retries:
                        # Превышено число попыток – помечаем как failed
                        # (можно отправить в DLQ или просто логировать).
                        self._logger.error(
                            f"Webhook failed after {new_retry_count} "
                            f"attempts: {event.id}"
                        )
                        await _outbox_repository.mark_completed_or_failed(
                            event_id=event.id,
                            status=WebhookStatus.FAILED,
                        )
                    else:
                        delay = (
                            settings.base_retry_delay *
                            (2 ** (new_retry_count - 1))
                        )
                        next_retry = (
                            datetime.now(timezone.utc) +
                            timedelta(seconds=delay)
                        )
                        await _outbox_repository.mark_pending(
                            event.id,
                            next_retry,
                            new_retry_count,
                        )
            except Exception as error:
                self._logger.error(
                    f"Error processing event {event.id}: {error}"
                )
                raise

    async def _process_pending_events(self):
        async with self.session_factory() as session:
            _outbox_repository = OutboxRepository(session)
            events = await _outbox_repository.get_pending_events(limit=500)

        event_tasks = [
            asyncio.create_task(
                self._process_event(
                    event=event,
                )
            )
            for event in events
        ]
        results = await asyncio.gather(
            *event_tasks,
            return_exceptions=True,
        )
        for res in results:
            if isinstance(res, Exception):
                self._logger.error(f"Task failed: {res}")
