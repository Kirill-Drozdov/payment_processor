from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

# Создаём базовый класс для будущих моделей.
Base = declarative_base()

# Создаём движок.
# Настройки подключения к БД передаём из переменных окружения,
# которые заранее загружены в файл настроек.
# dsn = (
#     'postgresql+asyncpg://'
#     f'{settings.postgres_user}:{settings.postgres_password}'
#     f'@{settings.postgres_host}:{settings.pgport}/{settings.postgres_db}'
# )

engine = create_async_engine(
    settings.postgres_dsn,
    echo=settings.echo_mode,
    future=True,
)
async_session = sessionmaker(
    engine,  # type: ignore
    class_=AsyncSession,
    expire_on_commit=False,
)  # type: ignore


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий, применяемый в DI."""
    async with async_session() as session:  # type: ignore
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
