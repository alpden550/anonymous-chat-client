import asyncio
from asyncio import Queue
from dataclasses import dataclass
from time import time

from async_timeout import timeout
from loguru import logger

ASYNC_TIMEOUT = 30


@dataclass
class ChatWatcherInterface:
    watcher: Queue

    async def watch_for_connection(self):
        while True:
            try:
                async with timeout(ASYNC_TIMEOUT):
                    msg = await self.watcher.get()
                    logger.info(f'{[int(time())]} Connection is alive. {msg}')
            except asyncio.TimeoutError:
                logger.error(f'{[int(time())]} timeout is elapsed.')
                raise ConnectionError

    async def main_func(self):
        await asyncio.gather(
            self.watch_for_connection(),
        )
