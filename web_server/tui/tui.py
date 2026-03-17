import importlib.metadata
import pathlib
from textual.app import App, ComposeResult
from textual import on
from textual.widgets import (
    Label,
    Select,
    Switch,
    Button,
    Footer,
    Header,
    Input,
    Rule,
    OptionList,
)
from textual.containers import (
    VerticalScroll,
    VerticalGroup,
    HorizontalGroup,
    Horizontal,
    Vertical,
)
from web_server.config import config
from web_server.config.config import (
    ConfigGoshs,
    ConfigServer,
    ConfigUpdog,
)
from web_server.tui.screens.open_folder import OpenFileScreen
from web_server.tui.screens.show_logs import ShowLogsScreen
from web_server.tui.utils import (
    DownloaderType,
    ServerType,
    copy_in_clipboard,
    generate_download_command,
    get_files_list,
    get_network_interfaces,
)
from web_server.tui.widgets.bordered_input import BorderedInput
from web_server.tui.widgets.double_click_optionlist import DoubleClickOptionList
from web_server.tui.widgets.goshs_form import GoshsForm
from web_server.tui.widgets.updog_form import UpdogForm
from web_server.tui.widgets.webserver_form import WebServerForm
from web_server.updog_server import UpdogServer
from web_server.webserver import WebServer
from textual.keys import Keys
from textual.binding import Binding

IS_SERVER_RUNNING = False

INPUT_WEB_DIRECTORY = "input_web_directory"
INPUT_TARGET_PATH = "input_target_path"
INPUT_PORT = "input_port"
INPUT_SEARCH_BAR = "input_search_bar"
LABEL_SWITCH = "label_switch"
BUTTON_BROWSE_FILE = "button_browse_file"
BUTTON_SHOW_LOGS = "button_show_logs"
SELECT_PROFILE = "select_profile"
SELECT_INTERFACE = "select_interface"
SELECT_SERVER_TYPE = "select_server_type"
SELECT_COMMAND_ID = "select_command_id"
OPTIONLIST_FILES = "optionlist_files"
SERVER_FORM = "server_form"
HORIZONTAL_GROUP_SERVER_CONFIG = "horizontal_group_server_config"


class TUI(App):
    BINDINGS = [
        Binding(Keys.ControlC, "custom_exit", "Quit", show=False, priority=True),
        Binding(Keys.ControlQ, "custom_exit", "Quit", show=False, priority=True),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self, args, config):
        self.CSS_PATH = "css/general.tcss"
        super().__init__()
        self.args = args
        self.title = f"🕸️ Web server v{importlib.metadata.version('web_server')}"
        self.webserver = None
        self.selected_config = None
        self.config = config

    def compose(self) -> ComposeResult:
        switch_webserver = Switch()

        input_target_path = BorderedInput(
            border_title="Target path",
            placeholder="e.g: C:\\Users\\Public\\",
            id=INPUT_TARGET_PATH,
        )

        vertical_group_config = VerticalGroup()
        vertical_group_config.border_title = "Server config"

        vertical_files = Vertical(id="vertical_files")
        vertical_files.border_title = "Files"

        select_profile = Select(
            prompt="Profile",
            options=[(key, key) for key in self.config["profiles"].keys()],
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
                        yield Button("Logs", id=BUTTON_SHOW_LOGS)
                    yield Select(
                        id=SELECT_SERVER_TYPE,
                        allow_blank=False,
                        options=[
                            (server_type.name, server_type.value)
                            for server_type in ServerType
                        ],
                    )
                    yield WebServerForm(SERVER_FORM, ConfigServer(ServerType.WEBSERVER))
                yield input_target_path
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

    def on_mount(self) -> None:
        if self.args.profile:
            try:
                select_profile = self.screen.query_one(f"#{SELECT_PROFILE}", Select)
                select_profile.value = self.args.profile
            except Exception:
                pass

        if self.args.auto:
            switch_webserver = self.screen.query_one(Switch)
            switch_webserver.toggle()

    async def on_switch_changed(self, event: Switch.Changed):
        global IS_SERVER_RUNNING

        ip = self.screen.query_one(f"#{SELECT_INTERFACE}", Select)
        web_directory = self.screen.query_one(f"#{INPUT_WEB_DIRECTORY}", Input).value
        port = self.screen.query_one(f"#{INPUT_PORT}", Input)

        if ip.is_blank() or not port.is_valid:
            self.notify("Parameters are incorrect !", severity="error")
            return

        if not IS_SERVER_RUNNING:
            if self.selected_config.type == ServerType.WEBSERVER.value:
                self.webserver = WebServer(self.selected_config)
            elif self.selected_config.type == ServerType.UPDOG.value:
                self.webserver = UpdogServer(self.selected_config)

            self.webserver.start()

            web_directory = self.screen.query_one(
                f"#{INPUT_WEB_DIRECTORY}", Input
            ).value
            web_directory_optionlist = self.screen.query_one(
                f"#{OPTIONLIST_FILES}", DoubleClickOptionList
            )
            web_directory_optionlist.add_options(get_files_list(web_directory))

            self.notify(
                f"Web server started on {ip.value}:{port.value}!",
                severity="information",
            )
        else:
            self.webserver.stop()
            self.notify("Web server stoped !", severity="warning")

        IS_SERVER_RUNNING = event.value

    @on(OptionList.OptionSelected)
    def on_path_selected(self, event: OptionList.OptionSelected):
        command_id = self.screen.query_one(f"#{SELECT_COMMAND_ID}", Select)
        ip = self.screen.query_one(f"#{SELECT_INTERFACE}").value
        port = self.screen.query_one(f"#{INPUT_PORT}").value
        target_path = self.screen.query_one(f"#{INPUT_TARGET_PATH}").value

        if command_id.is_blank():
            return

        web_path = f"http://{ip}:{port}/{event.option.prompt}"
        copy_in_clipboard(
            generate_download_command(
                DownloaderType(command_id.value), web_path, target_path
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
                get_files_list(web_directory, search=event.value)
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

    async def on_select_changed(self, event: Select.Changed):
        if event.select.id == SELECT_PROFILE and event.select.selection:
            await self.select_profile(event)
        elif event.select.id == SELECT_SERVER_TYPE:
            await self.select_server_type(event)

    # Check wether the profile is valid
    def is_profile_valid(
        self, profile_name: str, selected_profile: ConfigServer
    ) -> bool:
        error_message = None
        available_interface = [interface[0] for interface in get_network_interfaces()]

        # Check that the given interface exist
        if selected_profile.interface[0] not in available_interface:
            error_message = f"Profile '{profile_name}' is not valid, network interface '{selected_profile.interface}' doesn't seems to exist !"

        # Check that the given source folder exist
        if not pathlib.Path(selected_profile.directory).exists():
            error_message = f"Profile '{profile_name}' is not valid, directory path '{selected_profile.directory}' doesn't seems to exist !"

        # Check that the server type is valid
        try:
            ServerType(selected_profile.type)
        except ValueError:
            error_message = f"Profile '{profile_name}' is not valid, server type '{type}' is invalid !"

        if error_message:
            self.notify(error_message, severity="error")
            select_server_profile = self.query_one(f"#{SELECT_PROFILE}", Select)
            select_server_profile.clear()

            return False

        return True

    async def select_profile(self, event: Select.Changed):
        self.selected_config = config.toml_config_to_object(
            self.config["profiles"][event.select.selection]
        )

        if not self.is_profile_valid(event.select.selection, self.selected_config):
            return

        select_server_type = self.query_one(f"#{SELECT_SERVER_TYPE}", Select)
        form = self.query_one(f"#{SERVER_FORM}")
        await form.remove()

        with self.prevent(Select.Changed):
            # Do not trigger changed event, otherwise this will
            # erase the profile
            select_server_type.value = self.selected_config.type

        if self.selected_config.type == ServerType.WEBSERVER.value:
            await self.mount(
                WebServerForm(SERVER_FORM, self.selected_config),
                after=f"#{SELECT_SERVER_TYPE}",
            )
        elif self.selected_config.type == ServerType.UPDOG.value:
            await self.mount(
                UpdogForm(SERVER_FORM, self.selected_config),
                after=f"#{SELECT_SERVER_TYPE}",
            )
        elif self.selected_config.type == ServerType.GOSHS.value:
            await self.mount(
                GoshsForm(SERVER_FORM, self.selected_config),
                after=f"#{SELECT_SERVER_TYPE}",
            )
        else:
            await self.mount(
                WebServerForm(SERVER_FORM, ConfigServer()),
                after=f"#{SELECT_SERVER_TYPE}",
            )

    async def select_server_type(self, event: Select.Changed):
        profile_type = event.select.selection
        self.selected_config = None
        form = self.query_one(f"#{SERVER_FORM}")
        await form.remove()

        if profile_type == ServerType.WEBSERVER.value:
            await self.mount(
                WebServerForm(SERVER_FORM, ConfigServer()),
                after=f"#{SELECT_SERVER_TYPE}",
            )
        elif profile_type == ServerType.UPDOG.value:
            await self.mount(
                UpdogForm(SERVER_FORM, ConfigUpdog()),
                after=f"#{SELECT_SERVER_TYPE}",
            )
        elif profile_type == ServerType.GOSHS.value:
            await self.mount(
                GoshsForm(SERVER_FORM, ConfigGoshs()),
                after=f"#{SELECT_SERVER_TYPE}",
            )

    def action_custom_exit(self):
        if IS_SERVER_RUNNING:
            self.webserver.stop()

        self.exit()
