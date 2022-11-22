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
   and obtain game connection information.
10. Use response with any client.

"""
import asyncio
import platform
import socket
from dataclasses import dataclass
from itertools import islice
from time import sleep
from typing import Dict, Iterable, List, Literal, Self, Tuple

from .games import GameInfo


class AuthenticationError(Exception):
    """An error encountered during authenticating via the EAccess Protocol."""


class Actions:
    """EAccess Protocol action codes."""

    GetPasswordEcryptionKey = "K"
    AuthenticateAaccount = "A"
    GetGames = "M"
    GetGameCapabilities = "N"
    SelectGame = "G"
    GetCharacters = "C"
    SelectCharacter = "L"


@dataclass(frozen=True)
class Response:
    """EAccess server response.

    The raw payload is (usually) of the form
    b'{action}['\t']{body}\n' where the body is a tab separated
    list of values.
    """

    body: str
    request: bytes

    def split(self) -> List[str]:
        """Split tab separated response body values."""
        return self.body.split("\t")

    def pairs(self, key_start: int = 0) -> Iterable[Tuple[str, str]]:
        """Format response body as a list of (key, value) pairs, where
        the key / value are separated by a tab in the raw response.

        For example ["k0", "v0", "k1", "v1"] -> [("k0", "v0"), ("k1", "v1")]
        """
        val_start = key_start ^ 1
        vals = self.split()
        return zip(islice(vals, key_start, None, 2), islice(vals, val_start, None, 2))

    def json(self) -> Dict[str, str]:
        """Convert a body consisting of tab separated key=value pairs
        into a mapping.
        """
        if "=" in self.body:
            parts = (x.partition("=") for x in self.split())
            jbody = {i[0]: i[2] for i in parts}
        else:
            jbody = {k: v for k, v in self.pairs()}
        return jbody


class Client:
    """A client to communicate with the Simutronics authentication
    server via the EAccess Protocol used by non-web clients
    such as the Simutronics Game Entry (SGE).

    Authenticating a character profile
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

    # '\n' == 10 == 0x0A
    RECV_MESSAGE_END: int = 0x0A

    def __init__(self, host: str = "eaccess.play.net", port: int = 7900):
        self.host = host
        self.port = port
        self.conn: socket.socket = socket.create_connection((host, port))

    def close(self) -> Self:
        """Close socket connection."""
        self.conn.close()

    def recv(self) -> bytes:
        """Receive a message from the EAccess server. This consist of a
        byte array terminated with the ASCII linefeed character '\n'.

        Most any response fromt the EAccess
        """
        resp = bytes()
        while not resp or resp[-1] != self.RECV_MESSAGE_END:
            resp += self.conn.recv(1024)
        return resp

    def request(self, action: str, params: List[bytes | str] | None = None) -> Response:
        """Send a request to the EAccess server and wait for a response.

        Args:
            action: A single character code denoting the Protocol action.
                A summary list
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
        self.conn.send(msg)
        resp = self.recv().decode()
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

    def get_password_ecryption_key(self) -> str:
        """Get the 32 byte hashkey used to obfuscate the account password."""
        resp = self.request(Actions.GetPasswordEcryptionKey)
        return resp.body

    def get_games(self) -> Dict[str, str]:
        """Obtain a list of game code and desription pairs."""
        resp = self.request(Actions.GetGames)
        return resp.json()

    def authenticate_account(self, account: str, password: str) -> str:
        """Authenticate the account.

        Successive account-level protocol actions such as listing characters
        and game info.

        A successful raw authentication response looks like:
            b'A\tMYACCOUNT\tKEY\tb398f687206bcedfa42e80c9365ec42\tYOUR NAME\n'

        Returns:
            Account login key.

        """
        encryption_key = self.get_password_ecryption_key()
        encrypted_pw = self.encrypt_password(password, encryption_key)
        params = [account, encrypted_pw]
        resp = self.request(Actions.AuthenticateAaccount, params)
        if "KEY" not in resp.body:
            raise AuthenticationError(resp)
        try:
            key = resp.split()[-2]
        except IndexError:
            raise AuthenticationError(resp)
        return key

    def select_game(self, game: GameInfo | str) -> Dict[str, str]:
        """Request game informations for the specified game.

        Effectively logs the account into the game portal so that
        character information can be fetched.

        Args:
            game: A game code such as GS3 or GSF.

        Returns:
            A dict containing game info.
        """
        code = game.code if isinstance(game, GameInfo) else game
        resp = self.request(Actions.SelectGame, [code])
        return resp.json()

    def get_characters(self) -> Dict[str, str]:
        """Get character names and codes.

        Returns:
            A map of character name -> character code.
        """
        resp = self.request(Actions.GetCharacters)
        # Response starts with four metadata values
        # 1. total number char slots, 2. num character slots used 3. ?, 4. ?
        return {k: v for i, (v, k) in enumerate(resp.pairs()) if i > 1}

    def select_character(self, character: str) -> Dict[str, str]:
        """Select the specified character and obtain a character login key.

        Args:
            character: Character name.

        Raw response example
            b'L\tOK\tUPPORT=5535\tGAME=STORM\tGAMECODE=GS\tFULLGAMENAME=Wrayth\tGAMEFILE=WRAYTH.EXE\tGAMEHOST=storm.gs4.game.play.net\tGAMEPORT=10024\tKEY=8f478eed8c1f6db67bbbc115d1e3db0a\n'

        Returns:
            A map of character details, including the character login key.

        """
        characters = self.get_characters()
        code = characters.get(character.title())
        if code is None:
            raise AuthenticationError(f"Unknown character {character}.")
        resp = self.request(Actions.SelectCharacter, [code, "STORM"])
        return resp.json()

    def authenticate(
        self, account: str, password: str, game: str, character: str
    ) -> Dict[str, str]:
        """The main entry point which authenticates a character login session.

        The game and character selection process ties the character to the
        login key, which is sent by the game connection client.

        Returns:
            A dict containing login information that can be used by game
                clients to establish a connection. An example for Gemstone IV is
                {
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
        self.authenticate_account(account, password)
        self.select_game(game)
        connection_info = self.select_character(character)
        return connection_info
