import asyncio
from asyncio import Queue
from dataclasses import dataclass

from loguru import logger


@dataclass
class ChatWatcherInterface:
    watcher: Queue

    async def watch_for_connection(self):
        while True:
            msg = await self.watcher.get()
            logger.info(msg)

    async def main_func(self):
        await asyncio.gather(
            self.watch_for_connection(),
        )
