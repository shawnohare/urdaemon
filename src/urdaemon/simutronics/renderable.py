from datetime import datetime

from lxml import html
from rich.text import Text



def event_to_html(raw: str) -> html.HtmlElement:
    """Parse a Game Event to an html."""
    raise NotImplementedError


def hl(element: html.HtmlElement) -> Text:
    """Given a parsed HTML element from the game feed find all
    tags with the noun attribute and apply the desired
    highlighting as specified in the config.
    """
    try:
        timestamp = float(element.xpath('prompt')[0].get('time'))
        isotime = datetime.fromtimestamp(timestamp).isoformat()
    except Exception:
        isotime = datetime.now().isoformat()

    nouns = set(item.get('noun') for item in element.iter())
    nouns.discard(None)
    text = Text(f'{element.text_content().strip()}\n{isotime}\n')
    # TODO: let user define custom prompt?

    text.highlight_words(words=nouns, style='blue')
    return text
    console.print(text)
