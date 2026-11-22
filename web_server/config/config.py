from pathlib import Path
import shutil
import tomllib
import json

ATTRIBUTE_SERVER_TYPE = "type"

def load_config_from_json(config_filename: str = ""):
    with open(AppConfig.CONFIG_FOLDER / config_filename, "r") as config_file:
        config_file_json = json.load(config_file)
        interface = config_file_json['interface']
        
        directory = config_file_json['directory']
        auth_password = config_file_json['auth_password']
        auth_username = config_file_json['auth_username']
        http_port = config_file_json['port']
        smb_port = config_file_json['smb_port']
        ftp_port = config_file_json['ftp_port']
        read_only = config_file_json['read_only']

        if config_file_json['smb_server']:
            server_type = "SMB"
        elif config_file_json['ftp']:
            server_type = "FTP"
        else:
            server_type = "HTTP"

    return ConfigGoshs(interface, http_port, smb_port, ftp_port, directory, auth_username, auth_password, server_type, read_only)

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


class ConfigGoshs:
    def __init__(
        self,
        interface: str = "127.0.0.1",
        http_port: int = 443,
        smb_port: int = 445,
        ftp_port: int = 21,
        directory: str = ".",
        username: str = "",
        password: str = "",
        server_type: str = "",
        read_only: bool = False,
    ):
        self.interface = interface
        self.http_port = http_port
        self.smb_port = smb_port
        self.ftp_port = ftp_port
        self.directory = directory
        self.username = username
        self.password = password
        self.server_type = server_type
        self.read_only = read_only
