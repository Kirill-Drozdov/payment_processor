from http import HTTPStatus

from fastapi import Header, HTTPException, Request
from faststream.rabbit import RabbitBroker


async def get_idempotency_key(
    idempotency_key: str = Header(..., alias="Idempotency-Key", max_length=255)
) -> str:
    """Извлекает обязательный заголовок Idempotency-Key."""
    if not idempotency_key:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    return idempotency_key


async def get_authentication_key(
    authentication_key: str = Header(
        ...,
        alias="X-API-Key",
        max_length=255,
    )
) -> str:
    """Извлекает обязательный заголовок X-API-Key для аутентификации."""
    if not authentication_key:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="X-API-Key header is required",
        )
    return authentication_key


async def get_rabbit_broker(request: Request) -> RabbitBroker:
    broker = request.app.state.rabbit_broker
    if broker is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="RabbitMQ broker not available",
        )
    return broker
