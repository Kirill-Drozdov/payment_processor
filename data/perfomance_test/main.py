"""
Нагрузочное тестирование FastAPI приложения с эндпоинтами /payments (POST) и
 /payments/{payment_id} (GET).

Использует aiohttp для асинхронных запросов.
Собирает статистику времени ответа для каждого эндпоинта.
"""

import argparse
import asyncio
import random
import statistics
import time
import uuid
from decimal import Decimal
from typing import List, Dict, Any

from aiohttp import ClientTimeout, ClientSession

# --- Конфигурация по умолчанию ---
DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_ITERATIONS = 5000        # количество сценариев (POST + GET)
DEFAULT_CONCURRENCY = 100        # количество параллельных воркеров
DEFAULT_TIMEOUT = 10            # таймаут на один запрос (сек)

# Данные для генерации запросов
CURRENCIES = ["USD", "EUR", "RUB"]
# WEBHOOK_URL = "http://example.com/webhook"
WEBHOOK_URL = "some_url"
AMOUNT_MIN = 10.00
AMOUNT_MAX = 100000.00


def generate_payment_data() -> Dict[str, Any]:
    """Генерирует случайные данные для POST /payments."""
    amount = Decimal(str(round(random.uniform(AMOUNT_MIN, AMOUNT_MAX), 2)))
    currency = random.choice(CURRENCIES)
    description = f"Test payment {uuid.uuid4().hex[:8]}"
    meta_data = {"source": "load_test", "random": random.randint(1, 1000)}
    webhook_url = WEBHOOK_URL
    return {
        "amount": str(amount),
        "currency": currency,
        "description": description,
        "meta_data": meta_data,
        "webhook_url": webhook_url,
    }


def generate_idempotency_key() -> str:
    """Генерирует уникальный ключ идемпотентности."""
    return str(uuid.uuid4())


class LoadTestStats:
    """Сбор статистики времени выполнения."""

    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.errors: int = 0

    def add(self, elapsed: float, success: bool = True):
        if success:
            self.times.append(elapsed)
        else:
            self.errors += 1

    def report(self) -> str:
        """Формирует отчёт по статистике."""
        if not self.times:
            return f"{self.name}: нет успешных запросов, ошибок: {self.errors}"
        n = len(self.times)
        min_t = min(self.times)
        max_t = max(self.times)
        mean_t = statistics.mean(self.times)
        # процентили
        sorted_times = sorted(self.times)
        p50 = sorted_times[int(n * 0.5)]
        p95 = sorted_times[int(n * 0.95)]
        p99 = sorted_times[int(n * 0.99)]
        return (
            f"{self.name}:\n"
            f"  Успешных запросов: {n}\n"
            f"  Ошибок: {self.errors}\n"
            f"  Время (сек): мин={min_t:.3f}, макс={max_t:.3f}, среднее={mean_t:.3f}\n"  # noqa
            f"  Процентили: 50%={p50:.3f}, 95%={p95:.3f}, 99%={p99:.3f}"
        )


async def perform_scenario(
    session: ClientSession,
    base_url: str,
    stats_post: LoadTestStats,
    stats_get: LoadTestStats,
    semaphore: asyncio.Semaphore,
) -> None:
    """
    Выполняет один сценарий: POST -> GET.
    """
    async with semaphore:
        # Генерация данных для запроса
        payment_data = generate_payment_data()
        idempotency_key = generate_idempotency_key()
        headers = {
            "Idempotency-Key": idempotency_key,
            "X-API-Key": "123",
        }

        # POST /payments
        post_url = f"{base_url}/payments"
        try:
            start = time.monotonic()
            async with session.post(
                post_url, json=payment_data, headers=headers
            ) as resp:
                elapsed = time.monotonic() - start
                if resp.status == 202:  # HTTPStatus.ACCEPTED
                    data = await resp.json()
                    payment_id = data.get("id")
                    stats_post.add(elapsed, success=True)
                else:
                    # Неуспешный ответ
                    await resp.read()  # чтобы освободить ресурс
                    stats_post.add(elapsed, success=False)
                    return  # прерываем сценарий, т.к. нет id для GET
        except Exception as e:  # noqa
            stats_post.add(0.0, success=False)
            return

        # GET /payments/{payment_id}
        # get_url = f"{base_url}/payments/{payment_id}"
        # try:
        #     start = time.monotonic()
        #     async with session.get(get_url, headers=headers) as resp:
        #         elapsed = time.monotonic() - start
        #         if resp.status == 200:  # HTTPStatus.OK
        #             stats_get.add(elapsed, success=True)
        #         else:
        #             await resp.read()
        #             stats_get.add(elapsed, success=False)
        # except Exception:
        #     stats_get.add(0.0, success=False)


async def run_load_test(
    base_url: str,
    iterations: int,
    concurrency: int,
    timeout: int,
) -> None:
    """
    Запуск нагрузочного теста.
    """
    stats_post = LoadTestStats("POST /payments")
    stats_get = LoadTestStats("GET /payments/{id}")

    semaphore = asyncio.Semaphore(concurrency)

    # Настройка клиента с таймаутом
    timeout_config = ClientTimeout(total=timeout)

    async with ClientSession(timeout=timeout_config) as session:
        # Создаём список задач (iterations штук)
        tasks = [
            perform_scenario(
                session,
                base_url,
                stats_post,
                stats_get,
                semaphore,
            )
            for _ in range(iterations)
        ]

        # Запускаем все задачи
        await asyncio.gather(*tasks)

    # Вывод отчёта
    print("\n=== РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ ===\n")
    print(stats_post.report())
    print()
    print(stats_get.report())
    print("\n=== ТЕСТ ЗАВЕРШЁН ===")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Нагрузочное тестирование FastAPI приложения (эндпоинты /payments)."  # noqa
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Базовый URL приложения (по умолчанию: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Количество сценариев (POST + GET). По умолчанию: {DEFAULT_ITERATIONS}",  # noqa
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Количество параллельных воркеров. По умолчанию: {DEFAULT_CONCURRENCY}",  # noqa
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Таймаут на один запрос (сек). По умолчанию: {DEFAULT_TIMEOUT}",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Запуск теста с параметрами: {args}")
    start_time = time.monotonic()
    asyncio.run(
        run_load_test(
            args.url,
            args.iterations,
            args.concurrency,
            args.timeout,
        )
    )
    total_elapsed = time.monotonic() - start_time
    print(f"\nОбщее время выполнения: {total_elapsed:.2f} сек")


if __name__ == "__main__":
    main()
