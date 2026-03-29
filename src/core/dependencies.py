from http import HTTPStatus

from fastapi import Header, HTTPException


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
