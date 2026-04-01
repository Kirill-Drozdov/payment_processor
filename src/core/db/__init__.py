"""Импорт моделей для Alembic."""
from core.db.models import OutboxEvent, Payment
from core.db.postgres import Base  # noqa
