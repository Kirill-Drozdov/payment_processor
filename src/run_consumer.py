import asyncio

from consumer.core.app import app
from core.logger import set_logger_config

if __name__ == '__main__':
    set_logger_config(
        level='INFO',
        app='consumer',
    )
    asyncio.run(app.run())
