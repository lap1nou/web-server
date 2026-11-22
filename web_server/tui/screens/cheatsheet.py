from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Markdown, Static, DirectoryTree, Button, Input
from textual.containers import Container, HorizontalGroup

from web_server.tui import utils
from web_server.tui.widgets.action_buttons import ID_CONFIRM_BUTTON, ActionButtons

ID_PATH_INPUT = "select_path_input"
HORIZONTAL_GROUP_SERVER_CONFIG = "horizontal_group_server_config"

ID_BUTTON_CLOSE = "button_close"
ID_BUTTON_COPY_1 = "button_copy_1"
ID_BUTTON_COPY_2 = "button_copy_2"
SMB_MOUNT = ""
SMB_MOUNT_DELETE = ""

class CheatsheetScreen(ModalScreen):
    def __init__(self, ip: str = "", smb_share: str = "", username: str = "", password: str = ""):
        super().__init__()
        self.ip = ip
        self.smb_share = smb_share
        self.username = username
        self.password = password

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = "📁 Cheatsheet"
        SMB_MOUNT = f'''
```pwsh
net use \\\\{self.ip}\\{self.smb_share} /user:{self.username} {self.password}
```
        '''
        SMB_MOUNT_DELETE = f'''
```pwsh
net use \\\\{self.ip}\\{self.smb_share} /delete
```
        '''
        with container:
            with HorizontalGroup(id=HORIZONTAL_GROUP_SERVER_CONFIG):
                yield Markdown(SMB_MOUNT)
                yield Button("📃", id=ID_BUTTON_COPY_1)
            with HorizontalGroup():
                yield Markdown(SMB_MOUNT_DELETE)
                yield Button("📃", id=ID_BUTTON_COPY_2)
            yield Button("Close", variant="error", id=ID_BUTTON_CLOSE)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_BUTTON_CLOSE:
            self.screen.dismiss()
        elif event.button.id == ID_BUTTON_COPY_1:
            utils.copy_in_clipboard(SMB_MOUNT)
        elif event.button.id == ID_BUTTON_COPY_2:
            utils.copy_in_clipboard(SMB_MOUNT_DELETE)