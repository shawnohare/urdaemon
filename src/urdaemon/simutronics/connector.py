import asyncio

import platform

from urdaemon.simutronics.eaccess import EAccessClient, authenticate
from urdaemon.config.loader import load_config

from urdaemon.connection import Connection

PROTOCOL: str = f"/FE:WRAYTH /VERSION:1.0.1.26 /P:{platform.system()} /XML\n"

async def connect(
        account: str = '',
        password: str = '',
        game: str = '',
        character: str = '',
        profile: str = '',
        eaclient: EAccessClient | None = None,
        read_separator=b'</prompt>\r\n'
        ) -> Connection:
    """Opens an asyncio connection to the Simutronics server using the
    game feed protocol utilized by Wrayth / Stormfront front-ends.

    """
    if profile:
        conf = load_config()['simutronics']
        profile_conf = conf['profiles'][profile]
        profile_conf.setdefault('character', profile)
        account_key = profile_conf.pop("account")
        account_conf = conf["accounts"][account_key]
        creds = account_conf | profile_conf

        account = creds['account']
        password = creds['password']
        game = creds['game']
        character = creds['character']

    # Authenticate
    sess = await authenticate(account, password, game, character, client=eaclient)

    # Talk to the game server and tell it which protocol to use.
    reader, writer = await asyncio.open_connection(sess.host, sess.port)
    writer.write(f"{sess.key}\n".encode())
    writer.write(PROTOCOL.encode())

    # Need to wait a moment for validation.
    for _ in range(2):
        await asyncio.sleep(0.3)
        writer.write(b"<c>\n")
    await writer.drain()

    # conn = Connection(reader=reader, writer=writer, read_separator=b'</prompt>')
    conn = Connection(reader=reader, writer=writer, read_separator=read_separator)
    return conn
