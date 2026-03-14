from textual.app import ComposeResult
from textual.widgets import Select, Button, Static
from textual.containers import (
    HorizontalGroup,
)
from textual.validation import Number
from web_server.config.config import ConfigUpdog
from web_server.tui.utils import get_network_interfaces
from web_server.tui.widgets.bordered_input import BorderedInput

INPUT_PORT = "input_port"
INPUT_WEB_DIRECTORY = "input_web_directory"
INPUT_PASSWORD = "input_password"
SELECT_INTERFACE = "select_interface"
BUTTON_BROWSE_FILE = "button_browse_file"


class UpdogForm(Static):
    def __init__(self, id: str = None, config: ConfigUpdog = None):
        super().__init__(id=id)
        self.interface = config.interface
        self.directory = config.directory
        self.port = config.port
        self.password = config.password

    def compose(self) -> ComposeResult:
        input_web_directory = BorderedInput(
            border_title="Web directory",
            placeholder="e.g: /opt/resources/",
            id=INPUT_WEB_DIRECTORY,
            value=self.directory,
        )
        input_port = BorderedInput(
            border_title="Port",
            placeholder="8080",
            validators=[Number(minimum=1, maximum=65535)],
            id=INPUT_PORT,
            type="integer",
            value=str(self.port),
        )
        input_password = BorderedInput(
            border_title="Password",
            placeholder="Password123!",
            id=INPUT_PASSWORD,
            value=self.password,
            password=True,
        )

        with HorizontalGroup():
            yield input_web_directory
            yield Button("📁", id=BUTTON_BROWSE_FILE)
        with HorizontalGroup():
            yield input_port
            yield Select(
                prompt="Listening interface",
                options=get_network_interfaces(),
                id=SELECT_INTERFACE,
                value=self.interface,
            )
        with HorizontalGroup():
            yield input_password
