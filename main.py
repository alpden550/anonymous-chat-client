import asyncio

import click

from interfaces import ChatReaderInterface, gui, ChatWriterInterface, ChatWatcherInterface


async def start_chat(host: str, port: int, output: str, token: str):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    watching_queue = asyncio.Queue()

    reader = ChatReaderInterface(
        host=host,
        port=port,
        messages=messages_queue,
        histories=history_queue,
        statuses=status_updates_queue,
        watchers=watching_queue,
        logfile=output,
    )
    writer = ChatWriterInterface(
        host=host,
        messages=messages_queue,
        sends=sending_queue,
        statuses=status_updates_queue,
        watchers=watching_queue,
        token=token,
    )
    watcher = ChatWatcherInterface(watcher=watching_queue)

    await asyncio.gather(
        reader.main_func(),
        writer.main_func(),
        watcher.main_func(),
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
    '-o',
    '--output',
    default='chat-log.txt',
    type=str,
    help='Path to file to write chat history',
    show_default=True,
)
@click.option(
    '-t',
    '--token',
    required=False,
    help='Token to authenticate'
)
def main(host: str, port: int, output: str, token: str):
    asyncio.run(start_chat(host=host, port=port, output=output, token=token))


if __name__ == '__main__':
    main()
