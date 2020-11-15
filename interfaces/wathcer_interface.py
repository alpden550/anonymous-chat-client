import asyncio
from asyncio import Queue
from dataclasses import dataclass
from time import time
from socket import gaierror
from async_timeout import timeout
from loguru import logger

ASYNC_TIMEOUT = 30
ASYNC_DELAY = 1


@dataclass
class ChatWatcherInterface:
    watcher: Queue
    host: str
    port: int

    async def watch_for_server(self):
        try:
            reader, writer = await asyncio.open_connection(host=self.host, port=self.port)
            await self.ping_pong(reader=reader, writer=writer)
        finally:
            writer.close()

    @staticmethod
    async def ping_pong(reader, writer):
        while True:
            try:
                async with timeout(ASYNC_TIMEOUT):
                    writer.write('ping'.encode())
                    await reader.readline()
                await asyncio.sleep(ASYNC_DELAY)
            except (gaierror, asyncio.TimeoutError):
                logger.error(f'{[int(time())]} no internet connection.')
                raise ConnectionError

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
            self.watch_for_server(),
            self.watch_for_connection(),
        )
