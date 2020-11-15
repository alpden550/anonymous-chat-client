import asyncio
import datetime
from asyncio import Queue
from dataclasses import dataclass
from time import time

import aiofiles

from interfaces import gui


@dataclass
class ChatReaderInterface:
    host: str
    port: int
    messages: Queue = None
    histories: Queue = None
    statuses: Queue = None
    watchers: Queue = None
    logfile: str = None

    async def open_connection(self):
        try:
            reader, writer = await asyncio.open_connection(host=self.host, port=self.port)
            self.statuses.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            await self.read_msgs(reader)
        finally:
            writer.close()

    async def read_msgs(self, reader):
        while True:
            line = await reader.readline()
            self.messages.put_nowait(line.decode())
            self.histories.put_nowait(line.decode())
            self.watchers.put_nowait(f'{[int(time())]} Connection is alive. New message in chat')

    async def save_msgs(self):
        formatted_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        async with aiofiles.open(self.logfile, 'a') as output:
            while True:
                msg = await self.histories.get()
                await output.write(f'[{formatted_time}] {msg}')

    async def main_func(self):
        await asyncio.gather(
            self.open_connection(),
            self.save_msgs(),
        )
