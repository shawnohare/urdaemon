import asyncio

from asyncio import StreamReader, StreamWriter

import platform

from urdaemon.simutronics.eaccess import authenticate
from urdaemon.config.loader import load_config


async def connect(credentials: dict[str, str]) -> tuple[StreamReader, StreamWriter]:
    """Opens an asyncio connection to the Simutronics server using the
    game feed protocol utilized by Wrayth / Stormfront front-ends.

    """
    if "profile" in credentials:
        config = load_config()
        profile = config["profiles"][credentials["profile"]]
        account = config["accounts"][profile["account"]]
        credentials = profile | account

    info = await authenticate(credentials)
    reader, writer = await asyncio.open_connection(info.host, info.port)
    writer.write(f"{info.key}\n".encode())
    writer.write(f"/FE:WRAYTH /VERSION:1.0.1.26 /P:{platform.system()} /XML\n".encode())

    # Need to wait a moment for validation.
    for _ in range(2):
        await asyncio.sleep(0.3)
        writer.write(b"<c>\n")
    await writer.drain()

    return reader, writer
