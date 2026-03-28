
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from api.v1 import payment
from core.config import settings


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
    if settings.trace_mode is True:

        @app.middleware('http')
        async def before_request(request: Request, call_next):
            response = await call_next(request)
            request_id = request.headers.get('X-Request-Id')
            if not request_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'detail': 'X-Request-Id is required'},
                )
            return response

    # Подключение роутеров.
    app.include_router(payment.router, prefix='/api/v1', tags=['Payment'])

    return app


app = get_app()
