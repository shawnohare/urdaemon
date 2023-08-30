import asyncio


class Connection:
    """Base class representing a high-level async stream to a game server."""

    def __init__(self,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter,
                 read_separator: bytes = b'\r\n',
                 write_separator: bytes = b'\r\n',
                 encoding: str = 'utf-8',
                 quit_command: str = 'exit',
    ):
        """
        Args:
            reader, writer: The underlying stream reader and writer such as
                returned from asyncio.open_connection
            read_separator: The separator to use when invoking the
                reader.readntil method, i.e., the separator between
                messages sent by the game server.
            write_separator: Suffix to append to all messages written to the
                game server.
            encoding: The underlying encoding used. Note that UTF-8
                and ASCII decodings are the same for the ASCII Unicode points
                in the lower 7-bits, i.e., [0, ..., 127].
            quit_command: The message to send to the game server to indicate
                the connection should close.
        """
        self.reader = reader
        self.writer = writer
        self.read_separator = read_separator
        self.write_separator = write_separator
        self.encoding = encoding
        self.quit_command = quit_command
        self._open: bool = True

    async def read(self) -> str:
        """Read a message from the game server."""
        # FIXME: Seems to cause hangup in ui as if something is being processed
        # infinitely.
        # raw_msg: bytes = await self.reader.readuntil(self.read_separator)
        try:
            raw_msg: bytes = await self.reader.readuntil(self.read_separator)
        except asyncio.IncompleteReadError:
            raw_msg: bytes = b''
            self._open = False
            # await asyncio.sleep(1)

        try:
            text = raw_msg.decode(self.encoding)
        except UnicodeDecodeError:
            text = str(raw_msg)
        return text

    async def write(self, text: str):
        """Send a message (e.g., a command) to the game server."""
        msg: bytes = text.encode(self.encoding) + self.write_separator
        self.writer.write(msg)
        await self.writer.drain()

    def is_open(self) -> bool:
        """Report whether the underlying stream writer is still open, i.e.,
        not closing or closed.
        """
        return self._open or not self.writer.is_closing()

    async def close(self):
        """Send the quit command text to the game and try to close the connection."""
        self._open = False
        await self.write(self.quit_command)
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as exc:
            print(exc)

