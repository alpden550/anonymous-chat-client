import asyncio

import click

import gui


async def read_msgs(host: str, port: int, queue: asyncio.Queue) -> None:
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)

        while True:
            line = await reader.readline()
            if not line:
                break
            queue.put_nowait(line.decode())
    finally:
        writer.close()


async def start_chat(host: str, port: int) -> None:
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    asyncio.gather(
        read_msgs(host=host, port=port, queue=messages_queue),
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
def main(host: str, port: int, token: str):
    asyncio.run(start_chat(host=host, port=port))


if __name__ == "__main__":
    main()
