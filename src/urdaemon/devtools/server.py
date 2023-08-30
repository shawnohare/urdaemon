"""Mock game server for testing purposes.

The game server will periodically send a random event and responds to a
small selection of commands such as

look
health
attack
exit

"""
import asyncio
from asyncio import StreamReader, StreamWriter

from random import sample, randint

from time import time

HOST = "localhost"  # all available interfaces
PORT = 8888


def prompt() -> str:
    return f'<prompt time="{int(time())}">&gt;</prompt>\r\n'


async def handle_connection(reader: StreamReader, writer: StreamWriter):
    """Called by the underlying server whenever a client connects.

    Game feed messages are randomly sent to the client at certain intervals and
    a small subset of commands are parsed.
    """
    addr = writer.get_extra_info("peername")
    writer.write(f'Welcome to Mock Game Server {addr}\r\n'.encode())
    await writer.drain()
    print(f"Connection from {addr!r}")

    async def read_loop():
        """Read, parse and respond to client commands."""
        while raw := await reader.readuntil(b"\r\n"):
            try:
                text = raw.decode()
            except Exception:
                text = str(raw)

            text = text.strip()
            csplit = text.split(" ")
            match csplit:
                case ["look"]:
                    resp = "You are in a darkly lit room."
                case ["health"]:
                    resp = "You are healthy."
                case ["attack", obj]:
                    resp = f"You swing your sword at the {obj}!"
                case ["exit"]:
                    # Handle a user exiting the game session.
                    print(f'ENDING GAME SESSION for {addr}!\r\n')
                    writer.write(f'ENDING GAME SESSION for {addr}!\r\n'.encode())
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
                    break
                case _:
                    resp = f"Invalid command: {text}"

            print(f'sending: {resp}')

            text = f'{resp}\r\n{prompt()}'
            writer.write(text.encode())
            await writer.drain()

    async def write_loop():
        """Simulate game server sending events."""
        message_set = [
            'A <a noun="goblin">grotesque goblin</a> hobbles in.',
            "A goblin advances toward you.",
            "A forest troll climbs over a boulder.",
            "A forest troll advances towards you!",
            "A troll swings a massive claymore at you!\nAS: +100, DS: +50, d100: 60, = +110\nAnd hits for +6 points of damage!",
            "A troll swings a massive claymore at you!\nAS: +100, DS: +50, d100: 1, = +51\nAnd misses!",
            "It begins to snow.\nHard.",
            "It begins to rain.\nHard.",
            "It begins to rain.\nLightly.",
            "It begins to snow.\nLightly.",
            "You wonder what you are doing here.",
        ]

        while not writer.is_closing():
            event = sample(message_set, k=1)[0]
            text = f'{event}\r\n{prompt()}'
            writer.write(text.encode())
            await writer.drain()
            print(f'sendin: {text}')
            await asyncio.sleep(randint(1, 5))

    # FIXME: The server seems to not really respond fast to user actions.
    asyncio.gather(read_loop(), write_loop())
    # asyncio.gather(read_loop())


async def main():
    server = await asyncio.start_server(handle_connection, HOST, PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


# ---------------------------------------------------------------------------
# a class based approach
# class ClientConnectionHandler:
#     """A class representing a client connection to the server."""

#     async def read_loop(self):
#         """Read messages up to \n and print."""
#         async for msg in self.reader:
#             print(f"< {msg}".encode())

#     async def write_loop(self):
#         """Continuously write a basic increment to the client."""
#         cnt = 0
#         while True:
#             msg = f"server sending {cnt}"
#             print(f"> {msg}")
#             cnt += 1
#             self.writer.write(msg.encode() + b"\r\n")
#             await self.writer.drain()
#             await asyncio.sleep(1)

#     async def callback(self, reader, writer):
#         """The underlying connection handler callback used when a new
#         client connects to the server.
#         """
#         self.reader = reader
#         self.writer = writer

#         addr = self.writer.get_extra_info("peername")
#         self.writer.write(f"you connected {addr}\r\n".encode())

#         await writer.drain()
#         await asyncio.gather(self.read_loop(), self.write_loop())


# class Server:
#     def __init__(self, host: str = "localhost", port: int = 8888):
#         self.host = host
#         self.port = port

#     async def run(self):
#         server = await asyncio.start_server(
#             client_connected_cb=ClientConnectionHandler().callback,
#             host=self.host,
#             port=self.port,
#         )
#         addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
#         print(f"Serving on {addrs}")
#         await server.serve_forever()


# if __name__ == "__main__":
#     server = Server()
#     asyncio.run(server.run())
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
