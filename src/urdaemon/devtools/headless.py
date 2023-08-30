"""Test a urdaemon proxy Server instance."""

import asyncio

from random import sample, randint

from urdaemon.engine import Server, Connection

async def simulate_user_input(urd: Server):
    """Simulate write events, e.g., a user submitting text."""
    commands = [
        "look",
        "attack goblin",
        "health",
        "attck troll",
        "bomb!!!"
    ]

    n = 0
    while not urd.connection.writer.is_closing():
        command = sample(commands, k=1)[0]
        await urd.hub.user_input.put(command)
        await asyncio.sleep(randint(1, 5))
        n += 1


async def main():
    print('Opening connection to socket.')
    reader, writer = await asyncio.open_connection('localhost', 8888)
    conn = Connection(reader, writer, read_separator=b'</prompt>\r\n')
    print('Starting proxy server.')
    server = Server(conn)

    # FIXME: urd server not forwarding messages from user_input queue.
    await asyncio.gather(simulate_user_input(server), server.run())


if __name__ == "__main__":
    asyncio.run(main())

