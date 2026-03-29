from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request

from schemas.payment import PaymentRequest, PaymentResponse
from service.payment_service import PaymentServiceABC, get_payment_service
from core.dependencies import get_idempotency_key

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
