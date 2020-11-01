import asyncio
from datetime import datetime

import aiofiles
import click

import gui


async def read_msgs(
    host: str, port: int, queue: asyncio.Queue, history_queue: asyncio.Queue,
) -> None:
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)

        while True:
            line = await reader.readline()
            if not line:
                break
            queue.put_nowait(line.decode())
            history_queue.put_nowait(line.decode())
    finally:
        writer.close()


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


async def send_msgs(host: str, port: int, queue: asyncio.Queue):
    while True:
        message = await queue.get()


async def start_chat(host: str, port: int, output: str) -> None:
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    asyncio.gather(
        load_history(logfile=output, queue=messages_queue),
        read_msgs(
            host=host,
            port=port,
            queue=messages_queue,
            history_queue=history_queue,
        ),
        write_history(history=history_queue, logfile=output),
        send_msgs(host=host, port=port, queue=sending_queue),
    )

    await gui.draw(messages_queue, sending_queue, status_updates_queue)


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
    asyncio.run(start_chat(host=host, port=port, output=output))


if __name__ == "__main__":
    main()
