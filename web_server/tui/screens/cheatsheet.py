from urllib.parse import quote

from textual.app import ComposeResult
from textual.containers import Center, Container, HorizontalGroup
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown

from web_server.tui import utils

ID_PATH_INPUT = "select_path_input"
HORIZONTAL_GROUP_SERVER_CONFIG = "horizontal_group_server_config"

ID_BUTTON_CLOSE = "button_close"
ID_BUTTON_COPY_1 = "button_copy_1"
ID_BUTTON_COPY_2 = "button_copy_2"
ID_BUTTON_COPY_3 = "button_copy_3"


class CheatsheetScreen(ModalScreen):
    def __init__(
        self,
        ip: str = "",
        port: int = 443,
        smb_share: str = "",
        username: str = "",
        password: str = "",
    ):
        super().__init__()
        self.ip = ip
        self.port = port
        self.smb_share = smb_share
        self.username = username
        self.password = password
        self.cmd_smb_mount = f'net use "\\\\{self.ip}\\{self.smb_share}" /user:"{self.username}" "{self.password}"'
        self.cmd_smb_mount_delete = f'net use "\\\\{self.ip}\\{self.smb_share}" /delete'
        self.cmd_upload = f'curl -k -T "$FILENAME" "https://{quote(self.username, safe="")}:{quote(self.password, safe="")}@{self.ip}:{self.port}/"'

    def compose(self) -> ComposeResult:
        container = Container()
        container.border_title = "📚 Cheatsheet"
        SMB_MOUNT = f"""
```bat
{self.cmd_smb_mount}
```
        """
        SMB_MOUNT_DELETE = f"""
```bat
{self.cmd_smb_mount_delete}
```
        """
        UPLOAD = f"""
```bat
{self.cmd_upload}
```
        """
        with container:
            with HorizontalGroup(id=HORIZONTAL_GROUP_SERVER_CONFIG):
                yield Markdown(SMB_MOUNT)
                yield Button("📃", id=ID_BUTTON_COPY_1)
            with HorizontalGroup():
                yield Markdown(SMB_MOUNT_DELETE)
                yield Button("📃", id=ID_BUTTON_COPY_2)
            with HorizontalGroup():
                yield Markdown(UPLOAD)
                yield Button("📃", id=ID_BUTTON_COPY_3)
            with Center():
                yield Button("Close", variant="error", id=ID_BUTTON_CLOSE)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == ID_BUTTON_CLOSE:
            self.screen.dismiss()
        elif event.button.id == ID_BUTTON_COPY_1:
            utils.copy_in_clipboard(self.cmd_smb_mount)
            self.screen.dismiss()
        elif event.button.id == ID_BUTTON_COPY_2:
            utils.copy_in_clipboard(self.cmd_smb_mount_delete)
            self.screen.dismiss()
        elif event.button.id == ID_BUTTON_COPY_3:
            utils.copy_in_clipboard(self.cmd_upload)
            self.screen.dismiss()
