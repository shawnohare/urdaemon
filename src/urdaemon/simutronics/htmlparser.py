from lxml import html
class HtmlParser:
    """An experimental lxml HTML parser for Simutronics feeds.
    It assumes a game server events are delimited by a <prompt> tag.
    This is equivalent to reading the game feed until b"</prompt>\r\n".
    """

    def __call__(self, text: str):
        raise NotImplementedError

