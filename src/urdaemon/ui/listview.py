from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Footer


class ListViewExample(App):

    # CSS_PATH = "list_view.css"

    def compose(self) -> ComposeResult:
        yield ListView(
            ListItem(Label("GemStone Prime")),
            ListItem(Label("Gemstone Platinum")),
            ListItem(Label("GameStone Shattered")),
            ListItem(Label("GemStone Prime Test")),
            ListItem(Label("Gemstone Prime Dev")),
            ListItem(Label("GameStone Shattered")),
        )
        yield Footer()


if __name__ == "__main__":
    app = ListViewExample()
    app.run()
