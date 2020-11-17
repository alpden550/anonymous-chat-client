import asyncio
import sys

import click
from anyio import create_task_group
from environs import Env

from interfaces import ChatReaderInterface, gui, ChatWriterInterface, ChatWatcherInterface


async def start_chat(host: str, port: int, output: str, token: str):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    async with create_task_group() as tg:
        await tg.spawn(gui.draw, messages_queue, sending_queue, status_updates_queue)
        await tg.spawn(
            handle_connection, host, port, messages_queue, sending_queue, status_updates_queue, output, token,
        )


async def handle_connection(
        host: str,
        port: int,
        messages: asyncio.Queue,
        sends: asyncio.Queue,
        statuses: asyncio.Queue,
        output: str,
        token: str = None,
):
    while True:
        history_queue = asyncio.Queue()
        watching_queue = asyncio.Queue()
        try:
            reader = ChatReaderInterface(
                host=host,
                port=port,
                messages=messages,
                histories=history_queue,
                statuses=statuses,
                watchers=watching_queue,
                logfile=output,
            )
            writer = ChatWriterInterface(
                host=host,
                messages=messages,
                sends=sends,
                statuses=statuses,
                watchers=watching_queue,
                token=token,
            )
            watcher = ChatWatcherInterface(watcher=watching_queue, host=host, port=port)
            async with create_task_group() as tg:
                await tg.spawn(reader.main_func)
                await tg.spawn(writer.main_func)
                await tg.spawn(watcher.main_func)
        except ConnectionError:
            pass


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
    '-o',
    '--output',
    default='chat-log.txt',
    type=str,
    help='Path to file to write chat history',
    show_default=True,
)
def main(host: str, port: int, output: str):
    env = Env()
    env.read_env()
    token = env('TOKEN', None)
    if token is None:
        click.echo('Token not found, please register user first.')
        sys.exit(1)

    try:
        asyncio.run(start_chat(host=host, port=port, output=output, token=token))
    except (KeyboardInterrupt, gui.TkAppClosed):
        pass


if __name__ == '__main__':
    main()
