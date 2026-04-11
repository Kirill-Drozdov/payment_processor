import datetime as dt
import logging

from faststream.rabbit import RabbitBroker

from consumer.payment_emulator import PaymentEmulator
from core.datatypes import PaymentStatus
from core.db.models import Payment
from core.db.postgres import async_session
from repository.outbox_repository import OutboxRepository
from repository.payment_repository import PaymentRepository
from schemas.events import PaymentCreatedEvent


async def handle_payment_created(
    event: PaymentCreatedEvent,
    broker: RabbitBroker,
) -> None:
    """
    Обработчик сообщения по ключу payment.created.v1.
    Выполняется в рамках FastStream-подписки.
    """
    _logger = logging.getLogger(__name__)

    _outbox_repository = OutboxRepository(
        session_maker=async_session,  # type: ignore
    )

    _logger.info(f"Received payment event: {event.payment_id}")

    async with async_session() as session:  # type: ignore
        _payment_repository = PaymentRepository(
            model=Payment,
            session=session,
        )
        payment = await _payment_repository.get(event.payment_id)

        if payment is None:
            _logger.error(f"Payment {event.payment_id} not found in DB")
            # Не можем обработать – отправляем в DLQ (выбросим исключение).
            raise ValueError(f"Payment {event.payment_id} not found")

        # Идемпотентность: если платеж уже не в статусе pending, пропускаем.
        if payment.status != PaymentStatus.PENDING:
            _logger.info(
                f"Payment {event.payment_id} already processed "
                f"(status={payment.status}), skipping"
            )
            return

    # Эмулируем обработку.
    result_status = await PaymentEmulator.process()

    now = dt.datetime.now(dt.timezone.utc)

    async with async_session() as session:  # type: ignore
        _payment_repository = PaymentRepository(
            model=Payment,
            session=session,
        )
        # Обновляем статус в БД.
        updated = await _payment_repository.update_status(
            payment_id=event.payment_id,
            status=result_status,
            processed_at=now,
        )

    if not updated:
        # Конкурентное обновление – кто-то другой уже обработал.
        _logger.warning(
            f"Payment {event.payment_id} was already updated concurrently"
        )
        return

    # Если платеж обработан, создаем outbox событие для webhook
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
        await _outbox_repository.create_event(
            payment_id=event.payment_id,
            webhook_url=payment.webhook_url,
            payload=webhook_payload,
        )
    _logger.info(
        f"Payment {event.payment_id} processed with"
        f" status {result_status.value}"
    )
