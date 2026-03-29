from abc import ABC, abstractmethod
from http import HTTPStatus
from functools import lru_cache
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Payment
from core.db.postgres import get_session
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
    ) -> None:
        self._payment_repository = payment_repository

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

        return await self._payment_repository.create(
            obj_in=payment,
            idempotency_key=idempotency_key,
        )

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
        )
    )
