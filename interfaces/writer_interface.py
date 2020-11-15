import asyncio
import json
from asyncio import Queue, StreamWriter
from dataclasses import dataclass
from tkinter import messagebox

from anyio import create_task_group

import exceptions
from interfaces import gui

ASYNC_DELAY = 3


@dataclass
class ChatWriterInterface:
    host: str
    port: int = 5050
    messages: Queue = None
    sends: Queue = None
    statuses: Queue = None
    watchers: Queue = None
    token: str = None

    async def open_connection(self):
        try:
            reader, writer = await asyncio.open_connection(host=self.host, port=self.port)
            self.statuses.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

            await reader.readline()
            await self.handle_user(reader=reader, writer=writer)
            await self.send_msgs(writer=writer)

        finally:
            writer.close()

    async def send_msgs(self, writer: StreamWriter):
        while True:
            msg = await self.sends.get()
            writer.write(f'{msg}\n\n'.encode())
            self.watchers.put_nowait('Message send.')
            await writer.drain()

    async def handle_user(self, reader, writer):
        if self.token:
            await self.authorize_chat_user(token=self.token, writer=writer)
            authorize_data = await reader.readline()
            if not json.loads(authorize_data):
                messagebox.showerror("Неверный токен", "Проверьте токен, сервер его не узнал.")
                raise exceptions.InvalidToken
            user = json.loads(authorize_data)['nickname']
            msg = f'Выполнена авторизация. Пользователь {user}.\n\n'

            self.messages.put_nowait(msg)
            self.statuses.put_nowait(gui.NicknameReceived(user))
            self.watchers.put_nowait('Authorization done')

    @staticmethod
    async def authorize_chat_user(token: str, writer: StreamWriter):
        writer.write(f'{token}\n'.encode())
        await writer.drain()

    async def main_func(self):
        async with create_task_group() as tg:
            await tg.spawn(self.open_connection)
