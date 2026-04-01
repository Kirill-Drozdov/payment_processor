import datetime as dt
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.future import select

from core.datatypes import PaymentStatus
from core.db.models import Payment
from repository.psql_repository import RepositoryPsql
from schemas.payment import PaymentRequest


class PaymentRepository(RepositoryPsql[Payment, PaymentRequest]):
    """Репозиторий для взаимодействия с объектами Платежа.
    """

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        stmt = select(Payment).where(
            Payment.idempotency_key == idempotency_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        obj_in: PaymentRequest,
        idempotency_key: str,
    ) -> Payment:
        obj_data = jsonable_encoder(obj_in)
        # Добавляем ключ в данные модели.
        obj_data["idempotency_key"] = idempotency_key
        db_obj = Payment(**obj_data)
        self._session.add(db_obj)
        await self._session.commit()
        await self._session.refresh(db_obj)
        return db_obj

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: dt.datetime,
    ) -> Payment | None:
        """Обновляет статус платежа и время обработки."""
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .where(Payment.status == PaymentStatus.PENDING)
        )
        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            payment.processed_at = processed_at
            await self._session.commit()
            await self._session.refresh(payment)
        return payment
