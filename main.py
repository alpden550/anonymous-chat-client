import asyncio
import json
from asyncio import Queue
from asyncio.streams import StreamWriter
from datetime import datetime
from tkinter import messagebox

import aiofiles
import click
from loguru import logger

import exceptions
import gui

ASYNC_DELAY = 2
TIMEOUT_WATCH = 10


async def read_msgs(host: str, port: int, messages: Queue, history: Queue, statuses: Queue, watchdog: Queue):
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        statuses.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
        while True:
            line = await reader.readline()
            messages.put_nowait(line.decode())
            history.put_nowait(line.decode())
            watchdog.put_nowait('New message in chat')
            await asyncio.sleep(1)
    finally:
        writer.close()


async def send_msgs(queue: Queue, writer: StreamWriter, watchdog: Queue):
    while True:
        msg = await queue.get()
        await submit_message(message=msg, writer=writer, watchdog=watchdog)


async def submit_message(message: str, writer: StreamWriter, watchdog: Queue):
    writer.write(f'{message}\n\n'.encode())
    watchdog.put_nowait('Submit message')
    await writer.drain()


async def save_history(history: Queue, output: str):
    async with aiofiles.open(output, 'a') as chat_log:
        while True:
            formatted_time = datetime.now().strftime("%d.%m.%Y %H:%M")
            message = await history.get()
            await chat_log.write(f'[{formatted_time}] {message}')


async def handle_user(
        host: str,
        port: int = 5050,
        token: str = None,
        messages: Queue = None,
        sends: Queue = None,
        statuses: Queue = None,
        watchdog: Queue = None,
):
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        statuses.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
        watchdog.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
        await reader.readline()

        if token:
            await authorize_chat_user(token=token, writer=writer, watchdog=watchdog)
            authorize_data = await reader.readline()

            if not json.loads(authorize_data):
                messagebox.showerror("Неверный токен", "Проверьте токен, сервер его не узнал.")
                raise exceptions.InvalidToken

            user = json.loads(authorize_data)['nickname']
            message = f'Выполнена авторизация. Пользователь {user}.\n\n'
            event = gui.NicknameReceived(user)
            statuses.put_nowait(event)
            messages.put_nowait(message)
            watchdog.put_nowait('Authorization done')
            await asyncio.sleep(ASYNC_DELAY)
            await send_msgs(queue=sends, writer=writer, watchdog=watchdog)
    finally:
        writer.close()


async def authorize_chat_user(token: str, writer: StreamWriter, watchdog: Queue):
    writer.write(f'{token}\n'.encode())
    watchdog.put_nowait('Prompt before auth')
    await writer.drain()


async def watch_for_connection(queue: Queue):
    while True:
        msg = await queue.get()
        logger.info(f'Connection is alive. {msg}')


async def start_chat(host: str, port: int, token: str, logfile: str):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    await asyncio.gather(
        handle_user(
            host=host,
            token=token,
            messages=messages_queue,
            sends=sending_queue,
            statuses=status_updates_queue,
            watchdog=watchdog_queue,
        ),
        read_msgs(
            host=host,
            port=port,
            messages=messages_queue,
            history=history_queue,
            statuses=status_updates_queue,
            watchdog=watchdog_queue
        ),
        save_history(history=history_queue, output=logfile),
        watch_for_connection(queue=watchdog_queue),

        gui.draw(messages_queue, sending_queue, status_updates_queue),
    )


@click.command()
@click.option(
    '-h',
    '--host',
    default='minechat.dvmn.org',
    help='Host to connect',
    show_default=True,
)
@click.option(
    '-p',
    '--port',
    default=5000,
    type=int,
    help='Port for connected host',
    show_default=True,
)
@click.option(
    '-t',
    '--token',
    required=False,
    help='Token to authenticate'
)
@click.option(
    '-o',
    '--output',
    default='chat-log.txt',
    type=str,
    help='Path to file to write chat history',
    show_default=True,
)
def main(host: str, port: int, token: str, output: str):
    asyncio.run(start_chat(host, port, token, output))


if __name__ == '__main__':
    main()
