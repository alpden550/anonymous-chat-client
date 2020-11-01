import asyncio
import time

import click

import gui


async def generate_msgs(queue: asyncio.Queue) -> None:
    while True:
        queue.put_nowait(f'Ping {round(time.time())}')
        await asyncio.sleep(1)


async def start_chat() -> None:
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    asyncio.gather(generate_msgs(messages_queue))

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
    asyncio.run(start_chat())


if __name__ == "__main__":
    main()
