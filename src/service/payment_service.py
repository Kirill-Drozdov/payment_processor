from abc import abstractmethod, ABC
from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.postgres import get_session
from core.db.models import Payment
from repository.payment_repository import PaymentRepository
from schemas.payment import PaymentRequest, PaymentResponse


class PaymentServiceABC(ABC):
    @abstractmethod
    async def create(
        self,
        payment: PaymentRequest,
        idempotency_key: str,
    ) -> PaymentResponse:
        ...

    @abstractmethod
    async def get(self, payment_id: UUID) -> PaymentResponse:
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
        existing = await self._payment_repository.get_by_idempotency_key(
            idempotency_key=idempotency_key,
        )
        if existing:
            return PaymentResponse.model_validate(existing)

        return await self._payment_repository.create(
            obj_in=payment,
            idempotency_key=idempotency_key,
        )

    async def get(self, payment_id: UUID) -> PaymentResponse:
        return await self._payment_repository.get(
            obj_id=payment_id,
        )


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
