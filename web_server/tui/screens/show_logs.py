from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, RichLog
from textual.containers import Container, Horizontal
from web_server.tui.widgets.action_buttons import (
    ID_ACTIONS_HORIZONTAL,
    ID_CANCEL_BUTTON,
)

ID_PATH_INPUT = "select_path_input"
BUTTON_REFRESH = "button_refresh"


class ShowLogsScreen(ModalScreen):
    def __init__(self, server, message: str = ""):
        super().__init__()
        self.message = message
        self.server = server

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = "🗒️ Server logs"

        with container:
            yield RichLog(highlight=True)
            yield Horizontal(
                Button("Refresh", id=BUTTON_REFRESH),
                Button.error("Cancel", id=ID_CANCEL_BUTTON),
                id=ID_ACTIONS_HORIZONTAL,
            )

    def on_mount(self):
        self.update_richlog()

    def update_richlog(self):
        richlog = self.query_one(RichLog)
        richlog.clear()

        for line in self.server.logs.queue:
            richlog.write(line)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == BUTTON_REFRESH:
            self.update_richlog()
        elif event.button.id == ID_CANCEL_BUTTON:
            self.app.pop_screen()
