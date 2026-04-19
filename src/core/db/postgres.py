from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

# Создаём базовый класс для будущих моделей.
Base = declarative_base()

engine = create_async_engine(
    settings.postgres_dsn,
    echo=settings.echo_mode,
    pool_size=20,         # количество постоянных соединений
    max_overflow=10,      # дополнительных при пике
    pool_timeout=45,
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
