# consumer/processor.py
from datetime import datetime
import logging

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.payment_processor import PaymentEmulator
from core.datatypes import PaymentStatus
from core.db.postgres import async_session
from core.db.models import Payment
from repository.outbox_repository import OutboxRepository
from repository.payment_repository import PaymentRepository
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
            model=Payment,
            session=session,
        )
        payment = await payment_repo.get(event.payment_id)

        if payment is None:
            logger.error(f"Payment {event.payment_id} not found in DB")
            # Не можем обработать – отправляем в DLQ (выбросим исключение)
            raise ValueError(f"Payment {event.payment_id} not found")

        # Идемпотентность: если платеж уже не в статусе pending, пропускаем
        if payment.status != PaymentStatus.PENDING:
            logger.info(
                f"Payment {event.payment_id} already processed "
                f"(status={payment.status}), skipping"
            )
            return

        # Эмулируем обработку
        result_status = await PaymentEmulator.process(
            amount=payment.amount,
            currency=payment.currency,
        )

        now = datetime.utcnow()
        # Обновляем статус в БД
        updated = await payment_repo.update_status(
            payment_id=event.payment_id,
            status=result_status,
            processed_at=now,
        )

        if not updated:
            # Конкурентное обновление – кто-то другой уже обработал
            logger.warning(
                f"Payment {event.payment_id} was already updated concurrently"
            )
            return

        # Если платеж обработан успешно, создаем outbox событие для webhook
        if (
            result_status == PaymentStatus.SUCCEEDED or
            result_status == PaymentStatus.FAILED
        ):
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
            f"Payment {event.payment_id} processed with"
            f" status {result_status.value}"
        )
