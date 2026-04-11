import asyncio
from contextlib import asynccontextmanager
import logging

from faststream import FastStream
from faststream.rabbit import Channel, RabbitBroker, RabbitQueue
from sqlalchemy.exc import TimeoutError as SATimeoutError

from consumer.processor import handle_payment_created
from consumer.worker import OutboxWorker
from core.config import settings
from core.db.postgres import async_session, engine
from core.logger import set_logger_config
from repository.outbox_repository import OutboxRepository
from schemas.events import PaymentCreatedEvent

set_logger_config(
    level='INFO',
    app='consumer',
)

# Глобальные объекты.
broker = RabbitBroker(
    url=settings.rabbitmq_url,
    default_channel=Channel(prefetch_count=settings.broker_prefetch_count),
)
outbox_worker = OutboxWorker(
    outbox_repository=OutboxRepository(
        session_maker=async_session,  # type: ignore
    ),
)

# Настраиваем очередь с Dead Letter Exchange.
payment_queue = RabbitQueue(
    name='payment.created.v1',
    durable=True,
    arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': 'payment.created.v1.dlq',
        'x-max-retries': 3,
    },  # type: ignore
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

logger = logging.getLogger()


@broker.subscriber(payment_queue)
async def on_payment_created(event: PaymentCreatedEvent):
    try:
        await handle_payment_created(event, broker)
    except SATimeoutError as e:
        logger.error(f'Database timeout for payment {event.payment_id}: {e}')
        # Дальше решаем судьбу сообщения (см. п.3)
        raise   # или обработать иначе
