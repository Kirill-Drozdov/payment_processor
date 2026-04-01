import asyncio

from consumer.core.app import app

if __name__ == '__main__':
    asyncio.run(app.run())
