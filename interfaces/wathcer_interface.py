from asyncio import Queue
from dataclasses import dataclass

from loguru import logger


@dataclass
class ChatWatcherInterface:
    watcher: Queue

    async def watch_for_connection(self):
        msg = await self.watcher.get()
        logger.info(msg)
