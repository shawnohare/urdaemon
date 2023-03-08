"""GemStone IV and DragonRealms use the EAccess Protocol to authenticate
accounts and link a login key to a particular character when establishing
a connection to the game server via non-web means such as the
Simutronics Game Entry (SGE).

Protocol Summary

Messages to the EAccess server are of the form
b'{action}[\t]{body}\n'
where the body is a tab separated list of parameters.

1. (optional) Send version Line. Example: AL4334 SGE16 1 14
   if version sent, server responds with CURRENT if current version.
2. Send K action to obtain password encryption key.
3. Server Sends password encryption key.
4. Send action A with account and encrypted password as body.
6. Send actions to obtain information about games.
7. Send ction G with game code as body (e.g., GS3) to select the game.
8. Send actions C to obtain information about charactors, such as a mapping
   from character name to character code.
9. Send Action L with character code as the body to select the character
   and obtain game session connection information.
10. Use response with any client.

"""
import asyncio
from dataclasses import asdict, dataclass, replace
from itertools import islice
from typing import Iterable


from urdaemon.simutronics.games import GameInfo


class AuthenticationError(Exception):
    """An error encountered during authenticating via the EAccess Protocol."""


class Actions:
    """EAccess Protocol action codes.

    - K (key) Server responses with password hash Key.
    - A (account). Fetch account login key.
    - M (manifest) Asks the server for a list of games
    - N (?) Asks server for game capabilities
    - G (game). Obtain game details.
    - C (characters). List available characters.
    - L (character login) Fetch character session login key.
    - F (?) SGE Sends it... Server response: NORMAL
    - B (?) zMUD Sends it... Server response: UNKNOWN
    - P (?) SGE Sends it w/ gamecode.. Server response: ?
    """

    GetPasswordEcryptionKey = "K"
    AuthenticateAccount = "A"
    GetGames = "M"
    GetGameCapabilities = "N"
    SelectGame = "G"
    GetCharacters = "C"
    SelectCharacter = "L"


@dataclass(frozen=True)
class Response:
    """EAccess server response.

    The raw payload is (usually) of the form
    b"{action}['\t']{body}\n"
    where the body is a tab separated list of values or alternating key value
    pairs."""

    body: str
    request: bytes

    def split(self) -> list[str]:
        """Split tab separated response body values."""
        return self.body.split("\t")

    def pairs(self, swap: bool = False) -> Iterable[tuple[str, str]]:
        """Format response body as a list of (key, value) pairs, where
        the key / value are separated by a tab in the raw response.

        For example ["k0", "v0", "k1", "v1"] -> [("k0", "v0"), ("k1", "v1")]

        Args:
            swap: If the flag is set, assume (value, key) pairs instead.
        """
        key_start = 0 if not swap else 1
        val_start = key_start ^ 1
        vals = self.split()
        return zip(islice(vals, key_start, None, 2), islice(vals, val_start, None, 2))

    def json(self) -> dict[str, str]:
        """Convert a body consisting of tab separated key=value pairs
        into a mapping.
        """
        if "=" in self.body:
            parts = (x.partition("=") for x in self.split())
            jbody = {i[0]: i[2] for i in parts}
        else:
            jbody = {k: v for k, v in self.pairs()}
        return jbody


@dataclass(frozen=True)
class SessionInfo:
    """Contains the game host, port and character login key used by
    the client to connect to the game server. This is the main
    data structure returned from the EAccess Protocol for
    authenticating a character session.

    Attrs:
        host: The game server host (GAMEHOST).
        port: The game server port (GAMEPORT).
        key: Session key (KEY).
        upport: Unclear what this is (UPPORT).
        game_code: The game code, which does not necessarily match the code
            in GameInfo. Unused to establish a connection (GAMECODE).
        frontend: Alias for (GAME).
        frontend_full_name: Alias for (FULLGAMENAME).
        frontend_exe: Name of the front-end executable (GAMEFILE).
        ok: Indicates if the character session selection response was valid.
    """

    host: str = "storm.gs4.game.play.net"
    port: int = 10024
    key: str = ""
    # Values below appear to be largely unused to establish a connection to
    # the game server.
    game_code: str = "GS"
    upport: int = 5535
    frontend: str = "STORM"
    frontend_name: str = "Wrayth"
    frontend_exe: str = "WRAYTH.EXE"
    ok: bool = True


@dataclass
class Credentials:
    account: str = ""
    password: str = ""
    game: str = ""
    character: str = ""
    profile: str = ""


class EAccessClient:
    """A client to communicate with the Simutronics authentication
    server via the EAccess Protocol used by non-web clients
    such as the Simutronics Game Entry (SGE).

    Selecting a character profile
    (a tuple of account, password, game, character) establishes a
    link between an account login key and character. Subsequent
    game client connections will instanstiate a game session for the
    profile's character.

    Confer
    - https://warlockclient.fandom.com/wiki/EAccess_Protocol
    - SGE Protocol: https://gswiki.play.net/SGE_protocol/saved_posts

    The basic summary of the Protocol

    1. Authenticate the account.
    2. Select a game.
    3. Select a character.

    Protocol Order (details)

    """

    def __init__(self, host: str = "eaccess.play.net", port: int = 7900):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter

    async def connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self.reader = reader
        self.writer = writer

    async def close(self):
        """Close socket connection."""
        self.writer.close()
        await self.writer.wait_closed()

    async def request(
        self, action: str, params: list[bytes | str] | None = None
    ) -> Response:
        """Send a request to the EAccess server and wait for a response.

        Args:
            action: A single character code denoting the Protocol action.
            params: A list of parameters to include in the message payload,
                e.g., the account name and encrypted password.

        A typical message is comprised of an action code and a tab
        delimited collection of positional string parameters terminated by
        a newline. For example
            - b'A\tMYACCOUNT\tHASHED_PASSWORD\n'
            - b'K\n'

        Returns:
            A response from the EAccess server stripped of initial
            action code and trailing newline.
        """
        # Only follow the code with a tab if there are actual arguments.
        params = params or []
        params.insert(0, action)
        msg = (
            b"\t".join(x if isinstance(x, bytes) else x.encode() for x in params)
            + b"\n"
        )
        self.writer.write(msg)
        await self.writer.drain()

        raw = await self.reader.readuntil(b"\n")
        resp = raw.decode("ascii")

        # Remove code prefix and subsequent tab if it exists and terminal newline.
        if resp.startswith(action):
            resp = resp[1:]
        resp = resp.strip("\n").strip("\t")
        return Response(body=resp, request=msg)

    @staticmethod
    def encrypt_password(password: str, hashkey: str) -> bytes:
        """Obfuscate an account password. Must be done prior to
        requesting a login key for a character login session.

        Returns:
            The hashed password as a possibly non-decodeable byte array.
        """
        pairs = zip(password.encode(), hashkey.encode())
        return bytes(((((c - 32) ^ k) + 32) for c, k in pairs))

    async def get_password_ecryption_key(self) -> str:
        """Get the 32 byte hashkey used to obfuscate the account password."""
        resp = await self.request(Actions.GetPasswordEcryptionKey)
        return resp.body

    async def get_games(self) -> dict[str, str]:
        """Obtain a list of game code and desription pairs."""
        resp = await self.request(Actions.GetGames)
        return resp.json()

    async def authenticate_account(self, account: str, password: str) -> str:
        """Login to the account.

        Successive account-level protocol actions such as listing characters
        and game info.

        A successful raw authentication response looks like:
            b'A\tMYACCOUNT\tKEY\tb398f687206bcedfa42e80c9365ec42\tYOUR NAME\n'

        Returns:
            Account login key.

        """
        encryption_key = await self.get_password_ecryption_key()
        encrypted_pw = self.encrypt_password(password, encryption_key)
        params = [account, encrypted_pw]
        resp = await self.request(Actions.AuthenticateAccount, params)
        if "KEY" not in resp.body:
            raise AuthenticationError(resp)
        try:
            key = resp.split()[-2]
        except IndexError:
            raise AuthenticationError(resp)
        return key

    async def select_game(self, game: GameInfo | str) -> dict[str, str]:
        """Request game informations for the specified game.

        Effectively logs the account into the game portal so that
        character information can be fetched.

        Args:
            game: A game code such as GS3 or GSF.

        Returns:
            A dict containing game info.
        """
        code = game.code if isinstance(game, GameInfo) else game
        resp = await self.request(Actions.SelectGame, [code])
        return resp.json()

    async def get_characters(self) -> dict[str, str]:
        """Get character names and codes.

        Response starts with four metadata values
        1. total number char slots
        2. num character slots used
        3. ?
        4. ?

        Returns:
            A map of character name -> character code.
        """
        resp = await self.request(Actions.GetCharacters)
        return {k: v for i, (v, k) in enumerate(resp.pairs()) if i > 1}

    async def select_character(
        self, character: str, frontend: str = "STORM"
    ) -> SessionInfo:
        """Select the specified character and obtain game session login info.

        The underlying action expects a character code obtained from the
        `get_characters` name to code mapping as well as what looks like
        a value (hardcoded to STORM) specifying either the game feed protocol
        or client.


        Args:
            character: Character name.
            frontend: STORM, WIZ, or AVALON.

        Raw response example
            b'L\tOK\tUPPORT=5535\tGAME=STORM\tGAMECODE=GS\tFULLGAMENAME=Wrayth\tGAMEFILE=WRAYTH.EXE\tGAMEHOST=storm.gs4.game.play.net\tGAMEPORT=10024\tKEY=8f478eed8c1f6db67bbbc115d1e3db0a\n'

        and converted into a dict
                {
                    'OK': '1',
                    'UPPORT': '5535',
                    'GAME': 'STORM',
                    'GAMECODE': 'GS',
                    'FULLGAMENAME': 'Wrayth',
                    'GAMEFILE': 'WRAYTH.EXE',
                    'GAMEHOST': 'storm.gs4.game.play.net',
                    'GAMEPORT': '10024',
                    'KEY': '49a87e31c0d88c8224e0f040aaa7615b',
                 }


        """
        characters = await self.get_characters()
        character_code = characters.get(character.title())
        if character_code is None:
            raise AuthenticationError(f"Unknown character {character}.")

        # NOTE: Seems that the "front-end" can be STORM, WIZ, AVALON?
        # We might want to only support STORM
        resp = await self.request(
            action=Actions.SelectCharacter,
            params=[character_code, frontend],
        )

        # Fix body to contain "=" separated keys.
        resp = replace(resp, body=resp.body.replace("OK\t", "OK=1\t"))
        jresp = resp.json()

        return SessionInfo(
            host=jresp["GAMEHOST"],
            port=int(jresp["GAMEPORT"]),
            key=jresp["KEY"],
            game_code=jresp["GAMECODE"],
            upport=int(jresp["UPPORT"]),
            frontend=jresp["GAME"],
            frontend_name=jresp["FULLGAMENAME"],
            frontend_exe=jresp["GAMEFILE"],
            ok=jresp.get("OK") == "1",
        )

    async def authenticate(
        self, account: str, password: str, game: str, character: str
    ) -> SessionInfo:
        """The main entry point which authenticates a character login session.

        The game and character selection process ties the character to the
        login key, which is sent by the game connection client.

        """
        await self.authenticate_account(account, password)
        await self.select_game(game)
        return await self.select_character(character)


async def authenticate(
    credentials: Credentials | dict[str, str],
    host: str = "eaccess.play.net",
    port: int = 7900,
) -> SessionInfo:
    """Authenticate a character login session.

    Returns:
        Game session connection details such as host, port, and session key
        that are used to establish a socket connection to the game server.
    """
    if isinstance(credentials, Credentials):
        credentials = asdict(credentials)
    client = EAccessClient(host=host, port=port)
    await client.connect()
    credentials.pop("profile", None)
    session_info = await client.authenticate(**credentials)
    await client.close()
    return session_info
