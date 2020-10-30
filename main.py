import asyncio
import time

import gui


async def generate_msgs(queue: asyncio.Queue) -> None:
    while True:
        queue.put_nowait(f'Ping {round(time.time())}')
        await asyncio.sleep(1)


async def main() -> None:
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    asyncio.gather(generate_msgs(messages_queue))

    await gui.draw(messages_queue, sending_queue, status_updates_queue)


if __name__ == "__main__":
    asyncio.run(main())
