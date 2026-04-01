from abc import ABC, abstractmethod
from functools import lru_cache
from http import HTTPStatus
from uuid import UUID

from fastapi import Depends, HTTPException
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Payment
from core.db.postgres import get_session
from core.dependencies import get_rabbit_broker
from repository.payment_repository import PaymentRepository
from schemas.payment import (
    PaymentDetailResponse,
    PaymentRequest,
    PaymentResponse,
)


class PaymentServiceABC(ABC):
    @abstractmethod
    async def create(
        self,
        payment: PaymentRequest,
        idempotency_key: str,
    ) -> PaymentResponse:
        ...

    @abstractmethod
    async def get(self, payment_id: UUID) -> PaymentDetailResponse:
        ...


class PaymentService(PaymentServiceABC):
    def __init__(
        self,
        payment_repository: PaymentRepository,
        broker: RabbitBroker,
    ) -> None:
        self._payment_repository = payment_repository
        self._broker = broker

    async def create(
        self,
        payment: PaymentRequest,
        idempotency_key: str,
    ) -> PaymentResponse:
        """Создает платеж.

        Args:
            payment (PaymentRequest): данные по платежу.
            idempotency_key (str): ключ идемпотентности.

        Returns:
            PaymentResponse: данные по созданному платежу.
        """
        existing = await self._payment_repository.get_by_idempotency_key(
            idempotency_key=idempotency_key,
        )
        if existing:
            return PaymentResponse.model_validate(existing)

        new_payment = await self._payment_repository.create(
            obj_in=payment,
            idempotency_key=idempotency_key,
        )

        event_data = {
            "payment_id": str(new_payment.id),
            "status": new_payment.status.value,
            "amount": str(new_payment.amount),
            "currency": new_payment.currency.value,
            "created_at": new_payment.created_at.isoformat(),
            "webhook_url": new_payment.webhook_url,
        }
        await self._broker.publish(
            message=event_data,  # type: ignore
            routing_key="payment.created.v1",
            exchange="",
            timeout=3,
        )

        return new_payment

    async def get(self, payment_id: UUID) -> PaymentDetailResponse:
        """Получить подробную информацию о платеже.

        Args:
            payment_id (UUID): id платежа.

        Raises:
            HTTPException: если платежа с таким id нет в БД.

        Returns:
            PaymentDetailResponse: подробная информация по платежу.
        """
        payment = await self._payment_repository.get(
            obj_id=payment_id,
        )
        if payment is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Payment with id '{payment_id}' not found.",
            )
        return payment


@lru_cache()
def get_payment_service(
    session: AsyncSession = Depends(get_session),
    broker: RabbitBroker = Depends(get_rabbit_broker),
) -> PaymentService:
    """Функция-провайдер для предоставления сервиса.

    Args:
        session: сессия для взаимодействия с БД.

    Returns:
        Объект PaymentService.
    """
    return PaymentService(
        payment_repository=PaymentRepository(
            model=Payment,
            session=session,
        ),
        broker=broker,
    )
