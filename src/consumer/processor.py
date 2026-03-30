# consumer/processor.py
import logging
from datetime import datetime

from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.db.postgres import async_session
from core.datatypes import PaymentStatus
from consumer.payment_processor import PaymentEmulator
from repository.payment_repository import PaymentRepository
from repository.outbox_repository import OutboxRepository
from schemas.events import PaymentCreatedEvent

logger = logging.getLogger(__name__)


async def handle_payment_created(
    event: PaymentCreatedEvent,
    broker: RabbitBroker,
) -> None:
    """
    Обработчик сообщения из очереди payment.created.v1.
    Выполняется в рамках FastStream-подписки.
    """
    logger.info(f"Received payment event: {event.payment_id}")

    async with async_session() as session:  # type: ignore
        payment_repo = PaymentRepository(
            model=None, session=session)  # type: ignore
        # Получаем платеж (можно расширить репозиторий)
        from core.db.models import Payment
        payment = await payment_repo.get(event.payment_id)

        if payment is None:
            logger.error(f"Payment {event.payment_id} not found in DB")
            # Не можем обработать – отправляем в DLQ (выбросим исключение)
            raise ValueError(f"Payment {event.payment_id} not found")

        # Идемпотентность: если платеж уже не в статусе pending, пропускаем
        if payment.status != PaymentStatus.PENDING:
            logger.info(
                f"Payment {event.payment_id} already processed (status={payment.status}), skipping")
            return

        # Эмулируем обработку
        result_status = await PaymentEmulator.process(payment.amount, payment.currency)

        # Обновляем статус в БД
        now = datetime.utcnow()
        updated = await payment_repo.update_status(event.payment_id, result_status, now)

        if not updated:
            # Конкурентное обновление – кто-то другой уже обработал
            logger.warning(
                f"Payment {event.payment_id} was already updated concurrently")
            return

        # Если платеж обработан успешно, создаем outbox событие для webhook
        if result_status == PaymentStatus.SUCCEEDED or result_status == PaymentStatus.FAILED:
            webhook_payload = {
                "payment_id": str(event.payment_id),
                "status": result_status.value,
                "amount": str(payment.amount),
                "currency": payment.currency.value,
                "processed_at": now.isoformat(),
            }
            outbox_repo = OutboxRepository(session)
            await outbox_repo.create_event(
                payment_id=event.payment_id,
                webhook_url=payment.webhook_url,
                payload=webhook_payload,
            )
            # Транзакция закоммитится после выхода из контекстного менеджера
        logger.info(
            f"Payment {event.payment_id} processed with status {result_status.value}")
