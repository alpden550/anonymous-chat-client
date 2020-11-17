import asyncio
from asyncio import Queue
from dataclasses import dataclass
from socket import gaierror
from time import time

from anyio import create_task_group
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
        reader, writer = await asyncio.open_connection(host=self.host, port=self.port)
        await self.ping_pong(reader=reader, writer=writer)

        writer.close()
        await writer.wait_closed()

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

    async def run(self):
        async with create_task_group() as tg:
            await tg.spawn(self.watch_for_server)
            await tg.spawn(self.watch_for_connection)
