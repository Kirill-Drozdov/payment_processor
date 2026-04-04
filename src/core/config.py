import os

from pydantic_settings import BaseSettings, SettingsConfigDict

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
    # RabbitMQ.
    rabbitmq_default_user: str = 'admin'
    rabbitmq_default_pass: str = 'admin'
    rabbit_host: str = 'localhost'
    rabbit_port: int = 5672
    # Общие настройки проекта.
    app_port: int = 8000
    project_name: str = 'PaymentProcessor'
    app_version: str = 'v0.0.1'

    # Consumer
    webhook_timeout: float = 10.0
    outbox_poll_interval: float = 1.0
    max_webhook_retries: int = 5
    base_retry_delay: float = 1.0

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.pgport}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_default_user}:{self.rabbitmq_default_pass}"
            f"@{self.rabbit_host}:{self.rabbit_port}/"
        )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
