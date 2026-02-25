import importlib.metadata
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
from textual.validation import Number
from web_server.tui.screens.open_folder import OpenFileScreen
from web_server.tui.screens.show_logs import ShowLogsScreen
from web_server.tui.utils import (
    DownloaderType,
    copy_in_clipboard,
    generate_download_command,
    get_files_list,
    get_network_interfaces,
)
from web_server.tui.widgets.bordered_input import BorderedInput
from web_server.tui.widgets.double_click_optionlist import DoubleClickOptionList
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
SELECT_COMMAND_ID = "select_command_id"
OPTIONLIST_FILES = "optionlist_files"


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
        self.config = config

    def compose(self) -> ComposeResult:
        switch_webserver = Switch()

        input_web_directory = BorderedInput(
            border_title="Web directory",
            placeholder="e.g: /opt/resources/",
            id=INPUT_WEB_DIRECTORY,
            value=self.args.directory,
        )
        input_port = BorderedInput(
            border_title="Port",
            placeholder="8080",
            validators=[Number(minimum=1, maximum=65535)],
            id=INPUT_PORT,
            type="integer",
            value=str(self.args.port),
        )
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
                    with HorizontalGroup():
                        yield Label("on/off", id=LABEL_SWITCH)
                        yield switch_webserver
                        yield HorizontalGroup()
                        yield Button("Logs", id=BUTTON_SHOW_LOGS)
                    with HorizontalGroup():
                        yield input_web_directory
                        yield Button("📁", id=BUTTON_BROWSE_FILE)
                    with HorizontalGroup():
                        yield input_port
                        yield Select(
                            prompt="Listening interface",
                            options=get_network_interfaces(),
                            id=SELECT_INTERFACE,
                            value="127.0.0.1",
                        )
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
            self.webserver = WebServer(
                host=ip.value, port=int(port.value), directory=web_directory
            )
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
        target_path = self.screen.query_one(f"#{INPUT_TARGET_PATH}").value

        if command_id.is_blank():
            return

        web_path = f"http://{ip}:{self.args.port}/{event.option.prompt}"
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
            self.app.push_screen(ShowLogsScreen(self.webserver.server))

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == SELECT_PROFILE:
            selected_profile = event.select.selection
            selected_config = self.config["profiles"][selected_profile]

            select_interface = self.query_one(f"#{SELECT_INTERFACE}", Select)
            network_interfaces = get_network_interfaces()

            for interface in network_interfaces:
                if selected_config["interface"] == interface[0]:
                    select_interface.value = interface[1]
                    break

            input_port = self.query_one(f"#{INPUT_PORT}", Input)
            input_port.value = str(selected_config["port"])

            input_directory = self.query_one(f"#{INPUT_WEB_DIRECTORY}", Input)
            input_directory.value = selected_config["directory"]

    def action_custom_exit(self):
        if IS_SERVER_RUNNING:
            self.webserver.stop()

        self.exit()
