from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request

from schemas.payment import PaymentRequest, PaymentResponse

router = APIRouter()


@router.post(
    '/payments',
    response_model=PaymentResponse,
    status_code=HTTPStatus.ACCEPTED,
    summary='Создание платежа',
    response_description='Информация по созданному платежу',
)
async def create_payment(
    payment: PaymentRequest
) -> PaymentResponse:
    """Информация по созданному платежу.

    - **payment_id**: id платежа.
    - **status**: статус.
    - **created_at**: дата создания.
    """
    return
