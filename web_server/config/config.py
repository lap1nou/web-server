from pathlib import Path
import shutil
import tomllib
import json

ATTRIBUTE_SERVER_TYPE = "type"
CONFIG_FOLDER = Path.home() / ".webserver_tui"
CONFIG_FILENAME = "config.toml"

def load_config_from_json(config_filename: str = ""):
    with open(CONFIG_FOLDER / config_filename, "r") as config_file:
        config_file_json = json.load(config_file)
        interface = config_file_json.get('interface', '127.0.0.1')

        directory = config_file_json.get('directory', '/workspace/web')
        auth_password = config_file_json.get('auth_password', '')
        auth_username = config_file_json.get('auth_username', '')
        http_port = config_file_json.get('port', 443)
        smb_port = config_file_json.get('smb_port', 445)
        ftp_port = config_file_json.get('ftp_port', 21)
        read_only = config_file_json.get('read_only', False)

        if config_file_json.get('smb_server', False):
            server_type = "SMB"
        elif config_file_json.get('ftp', False):
            server_type = "FTP"
        else:
            server_type = "HTTP"

    return ConfigGoshs(interface, http_port, smb_port, ftp_port, directory, auth_username, auth_password, server_type, read_only)


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
