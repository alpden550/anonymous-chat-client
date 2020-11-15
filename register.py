import asyncio
import json
from asyncio import StreamReader, StreamWriter

import aiofiles
import click


async def handle_register(host: str, port: int, username: str):
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        await reader.readline()
        await register_user(username=username, reader=reader, writer=writer)

    finally:
        writer.close()


async def register_user(username: str, reader: StreamReader, writer: StreamWriter):
    writer.write('\n'.encode())
    await reader.readline()

    writer.write(f'{username}\n'.encode())
    user_data = await reader.readline()
    await writer.drain()
    token = json.loads(user_data.decode()).get('account_hash')

    async with aiofiles.open('.env', 'w') as env:
        await env.write(f'token={token}\n')


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
    default=5050,
    type=int,
    help='Port for connected host',
    show_default=True,
)
@click.option(
    '-u',
    '--username',
    default='',
    type=str,
    help='Username',
    show_default=True,
)
def main(host: str, port: int, username: str):
    asyncio.run(handle_register(host=host, port=port, username=username))


if __name__ == '__main__':
    main()
