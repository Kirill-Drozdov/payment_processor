# core/payment_processor.py
import asyncio
from decimal import Decimal
import random
from uuid import UUID

from core.datatypes import PaymentStatus


class PaymentEmulator:
    """Эмулирует обработку платежа (2-5 сек, 90% успех)."""

    @staticmethod
    async def process(amount: Decimal, currency: str) -> PaymentStatus:
        """Возвращает succeeded или failed."""
        delay = random.uniform(2.0, 5.0)
        await asyncio.sleep(delay)

        # 90% успеха, 10% ошибки
        success = random.random() < 0.9
        return PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
