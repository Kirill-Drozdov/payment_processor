"""Модель с конфигурацией логгера."""

import os
from logging import config as logging_config


def set_logger_config(level: str, app: str) -> dict:
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DEFAULT_HANDLERS = ['console', 'file']  # Добавлен файловый хендлер

    # Путь к файлу лога (можно вынести в переменную окружения)
    LOG_FILE = os.getenv('LOG_FILE', f'logs/{app}.log')
    # Создаём директорию для логов, если её нет
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': LOG_FORMAT,
            },
            'default': {
                '()': 'uvicorn.logging.DefaultFormatter',
                'fmt': '%(levelprefix)s %(message)s',
                'use_colors': None,
            },
            'access': {
                '()': 'uvicorn.logging.AccessFormatter',
                'fmt': "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
            },
        },
        'handlers': {
            'console': {
                'level': level,
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'default': {
                'formatter': 'default',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'access': {
                'formatter': 'access',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            # Новый файловый хендлер с ротацией
            'file': {
                # Уровень для файла (можно изменить на INFO)
                'level': level,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_FILE,
                'maxBytes': 30 * 1024 * 1024,    # 30 МБ
                'backupCount': 30,               # 30 файлов ротации
                'encoding': 'utf-8',             # Поддержка кириллицы
                'formatter': 'verbose',          # Используем тот же формат, что и для консоли
            },
        },
        'loggers': {
            '': {
                'handlers': LOG_DEFAULT_HANDLERS,
                'level': level,
            },
            'uvicorn.error': {
                'level': level,
            },
            'uvicorn.access': {
                # Также пишем access-логи в файл (опционально)
                'handlers': ['access', 'file'],
                'level': level,
                'propagate': False,
            },
        },
        'root': {
            'level': level,
            'formatter': 'verbose',
            'handlers': LOG_DEFAULT_HANDLERS,    # Сюда тоже попадёт 'file'
        },
    }
    logging_config.dictConfig(LOGGING)
    return LOGGING
