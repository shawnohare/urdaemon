# based originally on: # https://github.com/wshanks/mudconsole
# Unfortunately the mudconsole app seems to use textualize <= 0.2, which
# introduced significant API changes.
import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Header, Input, TextLog

from rich.text import Text

# from rich.pretty import pprint
# from rich.text import Text
# from rich.se

from urdaemon.engine import Server, EventHub
from urdaemon.connection import Connection

from datetime import datetime


class StoryView(TextLog):
    """A view of main content received from the MUD server."""

    def __init__(self, hub: EventHub):
        super().__init__(id='story_view')
        self.hub = hub

    async def write_loop(self):
        """Read content posted to the StoryView channel, e.g.,
        from auto-generated commands and triggers, etc.
        """
        while text := await self.hub.fe_story_view.get():
            self.write(text)

    async def on_mount(self):
        """Launch coroutine in background."""
        # NOTE: This basically works! Just don't await the gather statement.
        asyncio.gather(self.write_loop())


class UserInput(Input):
    """Input box for commands to send to server"""

    def __init__(self, hub: EventHub):
         super().__init__(id='user_input')
         self.hub = hub

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Log command to game window and send command to game server."""
        value = message.value
        if value == ':exit':
            self.app.exit()


        # self.app.query_one(StoryView).write(Text(f'({datetime.now()}) > {value}'))
        # await self.hub.fe_story_view.put(f'({time.time()})> {value}')
        await self.hub.fe_user_input.put(value)
        self.value = ''



class MudUI(App):
    """Main application class"""

    def __init__(self, hub: EventHub, **kwargs):
        super().__init__(**kwargs)
        self.hub = hub

        # TODO: On mount, maybe set up a UI message router so that
        # various state updates can be displayed in info widgets
        # such as inventory, left / right hand, hp + wounds / mana.


    def compose(self) -> ComposeResult:
        # TODO: Make connection lazy to avoid startup lag.
        yield Header()
        yield StoryView(self.hub)
        yield UserInput(self.hub)



async def main():
    """Main entry point of the application"""
    reader, writer = await asyncio.open_connection('localhost', 8888)
    conn = Connection(reader, writer, read_separator=b'</prompt>\r\n')
    server = Server(conn)
    app = MudUI(hub=server.hub)
    # asyncio.gather(server.run())
    await asyncio.gather(server.run(), app.run_async())


if __name__ == "__main__":
    asyncio.run(main())
