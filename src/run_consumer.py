import asyncio
from contextlib import asynccontextmanager

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from consumer.processor import handle_payment_created
from consumer.worker import OutboxWorker
from core.config import settings
from core.db.postgres import async_session, engine
from schemas.events import PaymentCreatedEvent

# Глобальные объекты.
broker = RabbitBroker(settings.rabbitmq_url)
outbox_worker = OutboxWorker(async_session)

# Настраиваем очередь с Dead Letter Exchange.
payment_queue = RabbitQueue(
    name="payment.created.v1",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "payment.created.v1.dlq",
        "x-max-retries": 3,
    }  # type: ignore
)


@asynccontextmanager
async def lifespan():
    # Стартуем с outbox worker в фоне.
    task = asyncio.create_task(outbox_worker.start())
    yield
    task.cancel()
    await outbox_worker.stop()
    await engine.dispose()

app = FastStream(
    broker,
    lifespan=lifespan,
)


@broker.subscriber(payment_queue)
async def on_payment_created(event: PaymentCreatedEvent):
    await handle_payment_created(event, broker)


if __name__ == "__main__":
    asyncio.run(app.run())
