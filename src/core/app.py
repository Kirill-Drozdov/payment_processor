
from fastapi import FastAPI, Depends

from api.v1 import payment
from core.config import settings
from core.dependencies import get_authentication_key


def get_app() -> FastAPI:
    """Производит инициализацию приложения.

    Returns:
        Объект приложения FastAPI.
    """

    app = FastAPI(
        title=settings.project_name,
        docs_url='/docs',
        openapi_url='/openapi.json',
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
