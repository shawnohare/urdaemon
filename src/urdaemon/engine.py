"""Core engine / game server proxy.

"""

import asyncio
from asyncio.queues import Queue


from dataclasses import dataclass

from .connection import Connection


@dataclass
class Event:
    """Base event indicating an inbound message from the game server / urdaemon
    proxy server or an outbound game / client command.

    Attrs:
        raw: A raw string representation of the game server message or user
            command.
        text: A pretty printable version of the underlying raw text. typically
            this attribute is populated after raw game server text is parsed.
    """

    raw: str
    # created_at: float
    # parsed: dict
    # text: Text = field(default_factory=lambda: Text())

    # def __post_init__(self):
    #     # Populate the rich text field with the raw string by default.
    #     if self.raw and not self.text:
    #         self.text = Text(self.raw)


@dataclass
class Topic:
    """Read messages from one Queue and broadcast subscribers."""
    # sender: Queue
    subscribers: list[Queue]

    async def publish(self, event):
        """
        """
        for subscriber in self.subscribers:
            await subscriber.put(event)

    def subscribe(self, queue: Queue) -> int:
        """Subscribe a receiver queue to the topic. Messages that are
        published will be put on the added queue.

        Returns:
            The number of subscribers.
        """
        self.subscribers.append(queue)
        return len(self.subscribers)



@dataclass
class EventHub:
    """A collection of typed queues used for inter process communication.

    Generally we assume the following high-level routes of communication.

    FE user input -> Command Processor -> FE View (?) + Command Processor -> Game Server
    Game Server -> Game Event Parser -> FE View + Engine -> Game Server

    Attrs:
        story_view: Text to print to the main story window.
        user_input: Text sent from the front-end user input widget.


    """

    # front-end related channels
    # could also just do Queue[Event]
    # game_server_read: Queue[str] = Queue[str]()
    game_server_write: Queue[str] = Queue[str]()
    # user_input: Queue[str] = Queue[str]()

    game_event_raw: Queue[str] = Queue[str]()

    cmd_raw: Queue = Queue()
    cmd_parsed: Queue = Queue()
    cmd_processed: Queue = Queue()

    fe_story_view: Queue = Queue()
    fe_user_input: Queue[str] = Queue[str]()


    # handler channels
    # def publish(self, event: Event, *channels: Queue):
    #     """Send a message to the specified channels."""
    #     for chan in channels:
    #         chan.queue.


class Server:
    """Underlying game proxy server and scripting engine."""

    def __init__(self, connection: Connection, headless: bool = False):
        self.hub = EventHub()
        self.connection = connection
        self.game_event_topic = Topic(subscribers=[self.hub.game_event_raw])
        if not headless:
            self.game_event_topic.subscribe(self.hub.fe_story_view)

    async def run(self):

        async def read_game_server_events():
            """Read messages from the game connection stream and broadcast

            Will break the read loop if an empty message is encountered.
            """
            topic = self.game_event_topic
            while event := await self.connection.read():
                # await self.hub.fe_story_view.put(event)
                await topic.publish(event)

        async def write_game_server_events():
            """Write commands (user or engine generated) to the game server."""
            while self.connection.is_open():
                event = await self.hub.game_server_write.get()
                try:
                    await self.connection.write(event)
                except ConnectionResetError:
                    break

        async def process_user_input():
            """Write commands (user or engine generated) to the game server."""
            # TODO: Should we distinguish between connection open and "offline"
            # mode, where user can still issue internal commands?
            while event := await self.hub.fe_user_input.get():
                await self.hub.game_server_write.put(event)

        # FIXME: Can't read or write.
        await asyncio.gather(
            read_game_server_events(),
            write_game_server_events(),
            process_user_input(),
        )
        # await asyncio.gather(read_game_server_events())
        # while event := await self.connection.read():
            # await self.hub.game_server_read.put(event)
            # print(event)

