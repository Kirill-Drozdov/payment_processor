
import contextlib

from fastapi import Depends, FastAPI
from faststream.rabbit import RabbitBroker, RabbitQueue

from api.v1 import payment
from core.config import settings
from core.dependencies import get_authentication_key

_broker: RabbitBroker | None = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global _broker

    _broker = RabbitBroker(settings.rabbitmq_url)
    await _broker.connect()

    queue = RabbitQueue(
        name="payments.new",
        durable=True,
    )
    await _broker.declare_queue(queue)

    app.state.rabbit_broker = _broker

    yield

    # Закрытие соединения
    if _broker:
        await _broker.stop()
        _broker = None


def get_app() -> FastAPI:
    """Производит инициализацию приложения.

    Returns:
        Объект приложения FastAPI.
    """

    app = FastAPI(
        title=settings.project_name,
        docs_url='/docs',
        openapi_url='/openapi.json',
        lifespan=lifespan,
    )

    # Подключение роутеров.
    app.include_router(
        payment.router,
        prefix='/api/v1',
        tags=['Payment'],
        dependencies=[Depends(get_authentication_key)],
    )

    return app


app = get_app()
