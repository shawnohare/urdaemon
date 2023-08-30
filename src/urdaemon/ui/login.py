from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Input, TextLog, Header, Footer


class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        self.input_account_widget = Input(
            id="input-login-account", placeholder="Account Name"
        )
        yield self.input_account_widget
        self.input_password_widget = Input(
            id="input-login-password", placeholder="Password", password=True
        )
        yield self.input_password_widget

        yield TextLog()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        log = self.query_one(TextLog)
        if not self.input_password_widget.value:
            log.write(f"not doing anything: {message.value}")
        else:
            log.write(
                f"account={self.input_account_widget.value}, password={self.input_password_widget.value}"
            )
            self.app.push_screen("game_window")

        # self.query_one(Input).value = ''


class GameWindow(Screen):
    def compose(self) -> ComposeResult:
        self.input_command_widget = Input(
            id="input-command", placeholder="Enter command"
        )
        yield self.input_command_widget
        yield TextLog()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        tlog = self.query_one(TextLog)
        tlog.write(message.value)
        self.input_command_widget.value = ""


class FEApp(App):
    # FIXME: How to show login screen initially?
    SCREENS = {"login": LoginScreen(), "game_window": GameWindow()}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        # self.install_screen(LoginScreen(), name='login')
        # self.install_screen(GameWindow(), name='game_window')
        self.push_screen("login")


if __name__ == "__main__":
    app = FEApp()
    app.run()
