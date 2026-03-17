from pathlib import Path
import shutil
import tomllib
import json
from typing import Tuple
from web_server.tui.utils import (
    ServerType,
    find_interface_by_ip,
    find_interface_by_name,
)


class AppConfig:
    CONFIG_FOLDER = Path.home() / ".webserver_tui"
    CONFIG_FILENAME = "config.toml"

    def __init__(self, config_path: str = CONFIG_FOLDER / CONFIG_FILENAME):
        if not Path(config_path).is_file():
            Path(config_path).parent.mkdir(exist_ok=True)

            default_config_path = Path(__file__).parent / AppConfig.CONFIG_FILENAME
            shutil.copy(default_config_path, config_path)

        with open(config_path, "rb") as config_file:
            self.config = tomllib.load(config_file)


class ConfigServer:
    def __init__(
        self,
        type: str = "webserver",
        interface: Tuple[str] = ("lo", "127.0.0.1"),
        port: int = 8080,
        directory: str = None,
    ):
        self.type = type
        self.interface = interface
        self.port = port
        self.directory = directory


class ConfigUpdog(ConfigServer):
    def __init__(
        self,
        type: str = "updog",
        interface: Tuple[str] = ("lo", "127.0.0.1"),
        port: int = 8080,
        directory: str = None,
        password: str = None,
    ):
        ConfigServer.__init__(self, type, interface, port, directory)
        self.password = password


class ConfigGoshs(ConfigServer):
    def __init__(
        self,
        type: str = "goshs",
        interface: Tuple[str] = ("lo", "127.0.0.1"),
        port: int = 8080,
        directory: str = None,
        config_file: str = None,
    ):
        ConfigServer.__init__(self, type, interface, port, directory)
        self.config_file = config_file


# Transform a TOML config into the corresponding Python object
def toml_config_to_object(selected_config):
    selected_config = selected_config.copy()
    profile_type = selected_config.get("type", ServerType.WEBSERVER)

    original_interface_name = selected_config.get("interface", None)
    selected_config["interface"] = find_interface_by_name(
        selected_config.get("interface", None)
    )

    if not selected_config["interface"]:
        selected_config["interface"] = (original_interface_name, "")

    if profile_type == ServerType.WEBSERVER.value:
        return ConfigServer(**selected_config)
    elif profile_type == ServerType.UPDOG.value:
        return ConfigUpdog(**selected_config)
    elif profile_type == ServerType.GOSHS.value:
        # This case is a bit special, we first need to parse the config file
        with open(selected_config.get("config_file"), "r") as goshs_config:
            json_config = json.load(goshs_config)
            return ConfigGoshs(
                interface=find_interface_by_ip(json_config["interface"]),
                port=json_config["port"],
                directory=json_config["directory"],
                config_file=selected_config.get("config_file"),
            )
