import asyncio
import json
import tkinter
from asyncio import StreamReader, StreamWriter

import aiofiles
import click


async def handle_register(host: str, port: int, username: str):
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        await reader.readline()
        token = await register_user(username=username, reader=reader, writer=writer)
        await save_user_token(token=token)
    finally:
        writer.close()
        await writer.wait_closed()


async def register_user(username: str, reader: StreamReader, writer: StreamWriter):
    writer.write('\n'.encode())
    await reader.readline()

    writer.write(f'{username}\n'.encode())
    user_data = await reader.readline()
    await writer.drain()
    token = json.loads(user_data.decode()).get('account_hash')
    return token


async def save_user_token(token):
    async with aiofiles.open('.env', 'w') as env:
        await env.write(f'TOKEN={token}\n')


def draw(host: str, port: int):
    root = tkinter.Tk()
    root.title('Регистрация в чате майнкрафтера')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 500, 400
    x = screen_width / 2 - width / 2
    y = screen_height / 2 - height / 2
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))

    f_name = tkinter.Frame(root)

    name_label = tkinter.Label(f_name, text='Имя:')
    name_entry = tkinter.Entry(f_name, width=70)
    token_label = tkinter.Label(width=70, height=10, text='Введите имя или никнейм, и нажмите зарегистрироваться')

    reg_button = tkinter.Button(text="Зарегистрироваться",
                                width=150,
                                height=4,
                                highlightbackground="lightblue",
                                )
    reg_button['command'] = lambda: handle_entered_name(name_entry, host, port, root)

    f_name.pack()
    name_label.pack(side=tkinter.TOP, padx=100, pady=30)
    name_entry.pack(side=tkinter.TOP, padx=100, pady=10)
    reg_button.pack(side=tkinter.TOP, padx=100, pady=10)
    token_label.pack(side=tkinter.BOTTOM, padx=10, pady=5)

    root.mainloop()


def handle_entered_name(name_entry, host, port, root):
    username = name_entry.get()
    if username:
        asyncio.run(handle_register(host=host, port=port, username=username))
        root.quit()


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
def main(host: str, port: int):
    draw(host=host, port=port)


if __name__ == '__main__':
    main()
