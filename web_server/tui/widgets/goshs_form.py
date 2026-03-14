from textual.app import ComposeResult
from textual.widgets import Button, Static
from textual.containers import (
    HorizontalGroup,
)
from web_server.config.config import ConfigGoshs
from web_server.tui.widgets.bordered_input import BorderedInput

INPUT_GOSHS_CONFIG = "input_goshs_config"
BUTTON_BROWSE_FILE = "button_browse_file"

class GoshsForm(Static):
    def __init__(self, id: str = None, config: ConfigGoshs = None):
        super().__init__(id=id)
        self.config_file = config.config_file

    def compose(self) -> ComposeResult:
        input_goshs_config = BorderedInput(
            border_title="Goshs config file",
            placeholder="e.g: /opt/resources/",
            id=INPUT_GOSHS_CONFIG,
            value=self.config_file,
        )

        with HorizontalGroup():
            yield input_goshs_config
            yield Button("📁", id=BUTTON_BROWSE_FILE)
