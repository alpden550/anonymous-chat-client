import asyncio
import json
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime

import aiofiles
import click

import gui


ASYNC_DELAY = 2


def sanitize_text(text: str) -> str:
    return text.replace('\n', '')


async def read_msgs(
    reader: StreamReader, queue: asyncio.Queue, history_queue: asyncio.Queue,
) -> None:
    while True:
        line = await reader.readline()
        if not line:
            break
        queue.put_nowait(line.decode())
        history_queue.put_nowait(line.decode())


async def write_history(history: asyncio.Queue, logfile: str):
    while True:
        formatted_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        async with aiofiles.open(logfile, 'a') as history_file:
            message = await history.get()
            await history_file.write(f'[{formatted_time}] {message}')


async def load_history(logfile: str, queue: asyncio.Queue):
    template = '### CHAT HISTORY ###\n\n{}\n### END HISTORY ###\n\n'
    async with aiofiles.open(logfile) as history_file:
        history = await history_file.read()
        if history:
            queue.put_nowait(template.format(history))


async def send_msgs(host: str, port: int, queue: asyncio.Queue, writer: StreamWriter) -> None:
    while True:
        message = await queue.get()
        await submit_message(message=message, writer=writer)


async def submit_message(message: str, writer: StreamWriter) -> StreamWriter:
    sanitazed_message = sanitize_text(message)
    writer.write(f'{sanitazed_message}\n\n'.encode())
    await writer.drain()


async def authorize_chat_user(token: str, writer: StreamWriter) -> StreamWriter:
    writer.write(f'{token}\n'.encode())
    await writer.drain()


async def handle_user(
    host: str,
    port: int = 5050,
    token: str = None,
    messages_queue: asyncio.Queue = None,
    sending_queue: asyncio.Queue = None,
) -> None:
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        await reader.readline()

        if token:
            await authorize_chat_user(token=token, writer=writer)
            authorize_data = await reader.readline()
            user = json.loads(authorize_data)['nickname']
            message = f'Выполнена авторизация. Пользователь {user}.\n\n'
            messages_queue.put_nowait(message)
            await asyncio.sleep(ASYNC_DELAY)
            await send_msgs(host=host, port=port, queue=sending_queue, writer=writer),
    finally:
        writer.close()


async def start_chat(host: str, port: int, output: str, token: str) -> None:
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)

        asyncio.gather(
            handle_user(
                host=host,
                token=token,
                messages_queue=messages_queue,
                sending_queue=sending_queue,
            ),
            load_history(logfile=output, queue=messages_queue),
            read_msgs(
                reader=reader,
                queue=messages_queue,
                history_queue=history_queue,
            ),
            write_history(history=history_queue, logfile=output),
        )
        await gui.draw(messages_queue, sending_queue, status_updates_queue)
    finally:
        writer.close()


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
    asyncio.run(start_chat(host=host, port=port, output=output, token=token))


if __name__ == "__main__":
    main()
