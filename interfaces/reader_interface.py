import asyncio
import datetime
from asyncio import Queue
from dataclasses import dataclass

import aiofiles
from anyio import create_task_group

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
            await writer.wait_closed()

    async def read_msgs(self, reader):
        while True:
            line = await reader.readline()
            self.messages.put_nowait(line.decode())
            self.histories.put_nowait(line.decode())
            self.watchers.put_nowait('New message in chat')

    async def save_msgs(self):
        formatted_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        async with aiofiles.open(self.logfile, 'a') as output:
            while True:
                msg = await self.histories.get()
                await output.write(f'[{formatted_time}] {msg}')

    async def run(self):
        async with create_task_group() as tg:
            await tg.spawn(self.open_connection)
            await tg.spawn(self.save_msgs)
