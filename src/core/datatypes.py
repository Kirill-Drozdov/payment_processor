from enum import Enum as PyEnum


class PaymentStatus(str, PyEnum):
    """Статусы платежа."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Currency(str, PyEnum):
    """Допустимые валюты."""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
