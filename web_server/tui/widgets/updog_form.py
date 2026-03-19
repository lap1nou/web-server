from textual.app import ComposeResult
from textual.widgets import Select, Button, Static
from textual.containers import (
    HorizontalGroup,
)
from textual.validation import Number
from web_server.config.config import ConfigUpdog
from web_server.tui.widgets.bordered_input import BorderedInput

INPUT_PORT = "input_port"
INPUT_WEB_DIRECTORY = "input_web_directory"
INPUT_PASSWORD = "input_password"
SELECT_INTERFACE = "select_interface"
BUTTON_BROWSE_FILE = "button_browse_file"


class UpdogForm(Static):
    def __init__(
        self,
        id: str = None,
        interfaces: dict[str, str] = {},
        config: ConfigUpdog = None,
    ):
        super().__init__(id=id)
        self.config = config
        self.interfaces = interfaces

    def compose(self) -> ComposeResult:
        input_web_directory = BorderedInput(
            border_title="Web directory",
            placeholder="e.g: /opt/resources/",
            id=INPUT_WEB_DIRECTORY,
            value=self.config.directory,
        )
        input_port = BorderedInput(
            border_title="Port",
            placeholder="8080",
            validators=[Number(minimum=1, maximum=65535)],
            id=INPUT_PORT,
            type="integer",
            value=str(self.config.port),
        )
        input_password = BorderedInput(
            border_title="Password",
            placeholder="Password123!",
            id=INPUT_PASSWORD,
            value=self.config.password,
            password=True,
        )

        with HorizontalGroup():
            yield input_web_directory
            yield Button("📁", id=BUTTON_BROWSE_FILE)
        with HorizontalGroup():
            yield input_port
            yield Select(
                prompt="Listening interface",
                options=self.interfaces.items(),
                id=SELECT_INTERFACE,
                value=self.interfaces[self.config.interface],
            )
        with HorizontalGroup():
            yield input_password
