"""
An simulated game client session using asyncio streams API.
"""
import asyncio

from random import sample, randint

from urdaemon.connection import Connection

async def read_loop(connection: Connection):
    """Print all"""
    while not connection.writer.is_closing() and (msg := await connection.read()):
        print(msg)
    print('exiting from client read loop')


async def write_loop(connection: Connection):
    """Simulate write events, e.g., a user submitting text."""
    commands = [
        "look",
        "attack goblin",
        "health",
        "attck troll",
        "bomb!!!",
        "exit",
    ]

    n = 0
    while not connection.writer.is_closing():
        if n >= 10:
            command = 'exit'
        else:
            command = sample(commands, k=1)[0]
        print(f"> {command}\r\n")

        try:
            await connection.write(command)
            if command == 'exit':
                print('exiting from client write loop')
                break
        except ConnectionResetError:
            print('exiting from client write loop')
            break

        await asyncio.sleep(randint(1, 5))
        n += 1


async def main():
    reader, writer = await asyncio.open_connection("localhost", 8888)
    connection = Connection(reader, writer, read_separator=b'</prompt>\r\n')
    await asyncio.gather(read_loop(connection), write_loop(connection))


if __name__ == "__main__":
    asyncio.run(main())
