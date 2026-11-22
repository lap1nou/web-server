from textual.app import ComposeResult
from textual.validation import Number
from textual.widgets import Button, Select, Static
from textual.containers import (
    HorizontalGroup,
)
from web_server.config.config import ConfigGoshs
from web_server.tui.utils import MAX_PORT, MIN_PORT, get_network_interfaces
from web_server.tui.widgets.bordered_input import BorderedInput

INPUT_PORT = "input_port"
INPUT_WEB_DIRECTORY = "input_web_directory"
INPUT_PASSWORD = "input_password"
SELECT_INTERFACE = "select_interface"
SELECT_SERVER_TYPE = "select_server_type"
BUTTON_BROWSE_FILE = "button_browse_file"
BUTTON_SHOW_PASSWORD = "button_show_password"

class GoshsForm(Static):
    def __init__(self, id: str = None, config: ConfigGoshs = None):
        super().__init__(id=id)
        self.config = config

    def compose(self) -> ComposeResult:
        input_web_directory = BorderedInput(
            border_title="Web directory",
            placeholder="e.g: /opt/resources/",
            id=INPUT_WEB_DIRECTORY,
            value=self.config.directory,
        )
        input_port = BorderedInput(
            border_title="Port",
            placeholder="443",
            validators=[Number(minimum=MIN_PORT, maximum=MAX_PORT)],
            id=INPUT_PORT,
            type="integer",
            value=str(self.config.http_port),
        )
        input_password = BorderedInput(
            border_title="Password",
            placeholder="Password123!",
            id=INPUT_PASSWORD,
            value=self.config.password,
            password=True,
        )
        button_show_password = Button("👁️‍🗨️", id=BUTTON_SHOW_PASSWORD,)
        select_type = Select(
            prompt="Server type",
            options=[("HTTP", "HTTP"),("SMB", "SMB"),("FTP", "FTP")],
            id=SELECT_SERVER_TYPE,
        )

        with HorizontalGroup():
            yield input_web_directory
            yield Button("📁", id=BUTTON_BROWSE_FILE)
        with HorizontalGroup():
            yield Select(
                allow_blank=False,
                prompt="Listening interface",
                options= [(k, v) for k,v in get_network_interfaces().items()],
                id=SELECT_INTERFACE,
                value="127.0.0.1",
            )
            yield input_port
        with HorizontalGroup():
            yield input_password
            yield button_show_password
        yield select_type
