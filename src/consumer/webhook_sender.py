# consumer/webhook_sender.py
import httpx
import logging

logger = logging.getLogger(__name__)


async def send_webhook(url: str, payload: dict, timeout: float = 10.0) -> bool:
    """Отправляет POST-запрос на webhook URL. Возвращает True при успехе (статус 2xx)."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(
                f"Webhook sent to {url}, status {response.status_code}")
            return True
    except Exception as e:
        logger.error(f"Webhook to {url} failed: {e}")
        return False
