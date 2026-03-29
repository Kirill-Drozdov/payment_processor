from uuid import UUID
from http import HTTPStatus

from fastapi import APIRouter, Depends

from core.dependencies import get_idempotency_key
from schemas.payment import (
    PaymentDetailResponse,
    PaymentRequest,
    PaymentResponse,
)
from service.payment_service import PaymentServiceABC, get_payment_service

router = APIRouter()


@router.post(
    '/payments',
    response_model=PaymentResponse,
    status_code=HTTPStatus.ACCEPTED,
    summary='Создание платежа',
    response_description='Информация по созданному платежу',
)
async def create_payment(
    payment: PaymentRequest,
    idempotency_key: str = Depends(get_idempotency_key),
    payment_service: PaymentServiceABC = Depends(get_payment_service),
) -> PaymentResponse:
    """Информация по созданному платежу.

    - **payment_id**: id платежа.
    - **status**: статус.
    - **created_at**: дата создания.
    """
    return await payment_service.create(
        payment=payment,
        idempotency_key=idempotency_key,
    )


@router.get(
    '/payments/{payment_id}',
    response_model=PaymentDetailResponse,
    status_code=HTTPStatus.OK,
    summary='Данные по платежу',
    response_description='Подробные данные по платежу',
)
async def get_payment(
    payment_id: UUID,
    payment_service: PaymentServiceABC = Depends(get_payment_service),
) -> PaymentDetailResponse:
    """Подробные данные по платежу.

    - **payment_id**: id платежа.
    - **status**: статус.
    - **created_at**: дата создания.
    - **amount**: сумма.
    - **currency**: валюта.
    - **description**: описание.
    - **meta_data**: мета информация.
    - **webhook_url**: url для отправки webhook.
    - **processed_at**: время обработки.
    - **updated_at**: время обновления.
    - **idempotency_key**: ключ идемпотентности.
    """
    return await payment_service.get(payment_id=payment_id)
