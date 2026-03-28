from logging import config as logging_config
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING

# Применяем настройки логирования.
logging_config.dictConfig(LOGGING)

# Корень проекта.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Настройки проекта."""
    # Настройки Postgres.
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'postgres'
    postgres_host: str = 'localhost'
    pgport: int = 5432
    echo_mode: bool = False
    # Общие настройки проекта.
    app_port: int = 8000
    project_name: str = 'PaymentProcessor'
    app_version: str = 'v0.0.1'
    trace_mode: bool = False

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
