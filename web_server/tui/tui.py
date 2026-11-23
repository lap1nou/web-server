import importlib.metadata
import pathlib

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.keys import Keys
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Rule,
    Select,
    Switch,
)

from web_server.config.config import (
    CONFIG_FOLDER,
    ConfigGoshs,
    load_config_from_json,
)
from web_server.goshs_server import GoshsServer
from web_server.tui.screens.cheatsheet import CheatsheetScreen
from web_server.tui.screens.open_folder import OpenFileScreen
from web_server.tui.screens.show_logs import ShowLogsScreen
from web_server.tui.utils import (
    MAX_PORT,
    MIN_PORT,
    DownloaderType,
    FTPDownloaderType,
    IPFormat,
    SMBDownloaderType,
    copy_in_clipboard,
    generate_download_command,
    get_files_list,
    get_network_interfaces,
    ip_formats,
)
from web_server.tui.widgets.double_click_optionlist import DoubleClickOptionList
from web_server.tui.widgets.goshs_form import (
    BUTTON_SHOW_PASSWORD,
    CHECKBOX_READ_ONLY,
    INPUT_PASSWORD,
    SELECT_IP_FORMAT,
    SELECT_SERVER_TYPE,
    GoshsForm,
)

IS_SERVER_RUNNING = False

INPUT_WEB_DIRECTORY = "input_web_directory"
INPUT_PORT = "input_port"
INPUT_SEARCH_BAR = "input_search_bar"
LABEL_SWITCH = "label_switch"
BUTTON_BROWSE_FILE = "button_browse_file"
BUTTON_SHOW_LOGS = "button_show_logs"
SELECT_PROFILE = "select_profile"
SELECT_INTERFACE = "select_interface"
SELECT_COMMAND_ID = "select_command_id"
OPTIONLIST_FILES = "optionlist_files"
SERVER_FORM = "server_form"
HORIZONTAL_GROUP_SERVER_CONFIG = "horizontal_group_server_config"


class TUI(App):
    BINDINGS = [
        Binding(Keys.F1, "cheatsheet", "Cheatsheet", show=True),
        Binding(Keys.ControlC, "custom_exit", "Quit", show=False, priority=True),
        Binding(Keys.ControlQ, "custom_exit", "Quit", show=False, priority=True),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self):
        self.CSS_PATH = "css/general.tcss"
        super().__init__()
        self.title = f"🕸️ Web server v{importlib.metadata.version('web_server')}"
        self.webserver = None
        self.selected_config = None
        self.interfaces = get_network_interfaces()

    def compose(self) -> ComposeResult:
        switch_webserver = Switch()

        vertical_group_config = VerticalGroup()
        vertical_group_config.border_title = "Server config"

        vertical_files = Vertical(id="vertical_files")
        vertical_files.border_title = "Files"

        select_profile = Select(
            prompt="Profile",
            options=[
                (key.name, key.name)
                for key in list(pathlib.Path(CONFIG_FOLDER).glob("*.json"))
            ],
            id=SELECT_PROFILE,
        )

        yield Header()

        with Horizontal():
            with vertical_files:
                yield DoubleClickOptionList(id=f"{OPTIONLIST_FILES}")
            with VerticalScroll():
                with vertical_group_config:
                    yield select_profile
                    with HorizontalGroup(id=HORIZONTAL_GROUP_SERVER_CONFIG):
                        yield Label("on/off", id=LABEL_SWITCH)
                        yield switch_webserver
                        yield HorizontalGroup()
                        yield Button("🗒️", id=BUTTON_SHOW_LOGS, tooltip="Server logs")
                    yield GoshsForm(SERVER_FORM, ConfigGoshs(directory=""), self.interfaces)
                yield Select(
                    allow_blank=False,
                    prompt="Download command type",
                    options=[
                        (downloader_type.name, downloader_type.value)
                        for downloader_type in DownloaderType
                    ],
                    id=SELECT_COMMAND_ID,
                )
        yield Rule(line_style="heavy")
        yield Input(placeholder="🔍 Search...", id=INPUT_SEARCH_BAR)
        yield Footer()

    async def on_switch_changed(self, event: Switch.Changed):
        global IS_SERVER_RUNNING

        interface = None
        web_directory = None
        port = None

        web_directory_optionlist = self.screen.query_one(
            f"#{OPTIONLIST_FILES}", DoubleClickOptionList
        )

        try:
            interface = self.screen.query_one(f"#{SELECT_INTERFACE}", Select).value
            web_directory = self.screen.query_one(
                f"#{INPUT_WEB_DIRECTORY}", Input
            ).value
            port = self.screen.query_one(f"#{INPUT_PORT}", Input).value
        except Exception:
            pass

        # if self.is_profile_valid(port, None, web_directory):
        # return

        if not IS_SERVER_RUNNING:
            og = (
                CONFIG_FOLDER
                / self.screen.query_one(f"#{SELECT_PROFILE}", Select).value
            )

            self.selected_config.directory = self.query_one(
                f"#{INPUT_WEB_DIRECTORY}", Input
            ).value
            self.selected_config.password = self.query_one(
                f"#{INPUT_PASSWORD}", Input
            ).value
            self.selected_config.interface = self.query_one(
                f"#{SELECT_INTERFACE}", Select
            ).value
            self.selected_config.server_type = self.query_one(
                f"#{SELECT_SERVER_TYPE}", Select
            ).value
            self.selected_config.read_only = self.query_one(
                f"#{CHECKBOX_READ_ONLY}", Checkbox
            ).value

            if self.selected_config.server_type == "SMB":
                self.selected_config.smb_port = int(
                    self.query_one(f"#{INPUT_PORT}", Input).value
                )
            elif self.selected_config.server_type == "FTP":
                self.selected_config.ftp_port = int(
                    self.query_one(f"#{INPUT_PORT}", Input).value
                )
            else:
                self.selected_config.http_port = int(
                    self.query_one(f"#{INPUT_PORT}", Input).value
                )

            self.webserver = GoshsServer(self.selected_config, og)

            self.webserver.start()

            web_directory_optionlist.add_options(get_files_list(web_directory))

            self.notify(
                f"Web server started on {interface}:{port}!",
                severity="information",
            )

            IS_SERVER_RUNNING = event.value
        else:
            self.webserver.stop()
            web_directory_optionlist.clear_options()
            self.notify("Web server stoped !", severity="warning")
            IS_SERVER_RUNNING = event.value

    @on(OptionList.OptionSelected)
    def on_path_selected(self, event: OptionList.OptionSelected):
        command_id = self.screen.query_one(f"#{SELECT_COMMAND_ID}", Select)
        ip = self.screen.query_one(f"#{SELECT_INTERFACE}").value
        ip_format = self.screen.query_one(f"#{SELECT_IP_FORMAT}").value

        if ip_format != Select.NULL:
            ip = ip_formats(ip, IPFormat(ip_format))

        port = self.screen.query_one(f"#{INPUT_PORT}").value
        password = self.screen.query_one(f"#{INPUT_PASSWORD}").value
        username = self.selected_config.username
        filename = event.option.prompt
        protocol = self.screen.query_one(f"#{SELECT_SERVER_TYPE}").value.lower()
        smb_share = self.selected_config.smb_share

        if command_id.is_blank():
            return

        copy_in_clipboard(
            generate_download_command(
                command_id.value,
                protocol,
                ip,
                port,
                username,
                password,
                filename,
                smb_share,
            )
        )
        self.notify("Path copied to the clipboard !", severity="information")

    async def on_input_changed(self, event: Input.Changed):
        if event.input.id != INPUT_SEARCH_BAR or not IS_SERVER_RUNNING:
            return

        web_directory = self.screen.query_one(f"#{INPUT_WEB_DIRECTORY}", Input).value
        web_directory_optionlist = self.screen.query_one(
            f"#{OPTIONLIST_FILES}", OptionList
        )
        web_directory_optionlist.clear_options()

        if event.value:
            web_directory_optionlist.add_options(
                get_files_list(web_directory, search=f"*{event.value}*")
            )
        else:
            web_directory_optionlist.add_options(get_files_list(web_directory))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == BUTTON_BROWSE_FILE:

            def select_web_directory(path: str):
                self.screen.query_one(f"#{INPUT_WEB_DIRECTORY}", Input).value = path

            self.app.push_screen(
                OpenFileScreen("Choose a directory to serve files from:"),
                select_web_directory,
            )
        elif event.button.id == BUTTON_SHOW_LOGS and self.webserver:
            self.app.push_screen(ShowLogsScreen(self.webserver))
        elif event.button.id == BUTTON_SHOW_PASSWORD:
            password_input = self.screen.query_one(f"#{INPUT_PASSWORD}", Input)
            password_input.password = not password_input.password

    async def on_select_changed(self, event: Select.Changed):
        if event.select.id == SELECT_PROFILE and event.select.selection:
            await self.select_profile(event)
        elif event.select.id == SELECT_SERVER_TYPE and self.selected_config:
            server_type = event.select.selection

            if server_type == "SMB":
                self.query_one(f"#{INPUT_PORT}", Input).value = str(
                    self.selected_config.smb_port
                )
                self.query_one(f"#{SELECT_COMMAND_ID}", Select).set_options(
                    [
                        (downloader_type.name, downloader_type.value)
                        for downloader_type in SMBDownloaderType
                    ]
                )
            elif server_type == "FTP":
                self.query_one(f"#{INPUT_PORT}", Input).value = str(
                    self.selected_config.ftp_port
                )
                self.query_one(f"#{SELECT_COMMAND_ID}", Select).set_options(
                    [
                        (downloader_type.name, downloader_type.value)
                        for downloader_type in FTPDownloaderType
                    ]
                )
            else:
                self.query_one(f"#{INPUT_PORT}", Input).value = str(
                    self.selected_config.http_port
                )
                self.query_one(f"#{SELECT_COMMAND_ID}", Select).set_options(
                    [
                        (downloader_type.name, downloader_type.value)
                        for downloader_type in DownloaderType
                    ]
                )

    # Check wether the profile is valid
    def is_profile_valid(
        self,
        port: int = None,
        interface: str = None,
        directory: str = None,
        type: str = None,
    ) -> bool:
        error_message = None

        # Check that the port is ok
        if port and port not in range(MIN_PORT, MAX_PORT):
            error_message = f"Settings are invalid, port '{port}' is invalid !"

        # Check that the given interface exist
        if interface and interface not in self.interfaces.keys():
            error_message = f"Settings are invalid, network interface '{interface}' doesn't seems to exist !"

        # Check that the given source folder exist
        if directory and not pathlib.Path(directory).exists():
            error_message = f"Settings are invalid, directory path '{directory}' doesn't seems to exist !"

        if error_message:
            self.notify(error_message, severity="error")
            # select_server_profile = self.query_one(f"#{SELECT_PROFILE}", Select)
            # select_server_profile.clear()

            return False

        return True

    async def select_profile(self, event: Select.Changed):
        self.selected_config = load_config_from_json(event.select.selection)

        self.query_one(
            f"#{INPUT_WEB_DIRECTORY}", Input
        ).value = self.selected_config.directory
        self.query_one(
            f"#{INPUT_PASSWORD}", Input
        ).value = self.selected_config.password
        self.query_one(
            f"#{SELECT_INTERFACE}", Select
        ).value = get_network_interfaces().get(
            self.selected_config.interface, "127.0.0.1"
        )
        self.query_one(
            f"#{SELECT_SERVER_TYPE}", Select
        ).value = self.selected_config.server_type
        self.query_one(
            f"#{CHECKBOX_READ_ONLY}", Checkbox
        ).value = self.selected_config.read_only

        if self.selected_config.server_type == "SMB":
            self.query_one(f"#{INPUT_PORT}", Input).value = str(
                self.selected_config.smb_port
            )
        elif self.selected_config.server_type == "FTP":
            self.query_one(f"#{INPUT_PORT}", Input).value = str(
                self.selected_config.ftp_port
            )
        else:
            self.query_one(f"#{INPUT_PORT}", Input).value = str(
                self.selected_config.http_port
            )

    def action_custom_exit(self):
        if IS_SERVER_RUNNING:
            self.webserver.stop()

        self.exit()

    def action_cheatsheet(self) -> None:
        if self.selected_config:
            interface = self.query_one(
                f"#{SELECT_INTERFACE}", Select
            ).value
            http_port = self.query_one(
                f"#{INPUT_PORT}", Input
            ).value
            password = self.query_one(
                            f"#{INPUT_PASSWORD}", Input
                        ).value
            self.push_screen(
                CheatsheetScreen(
                    interface,
                    http_port,
                    self.selected_config.smb_share,
                    self.selected_config.username,
                    password,
                )
            )
