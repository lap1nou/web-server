import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

CONFIG_FOLDER = Path.home() / ".webserver_tui"


@dataclass
class ConfigGoshs:
    interface: str = "127.0.0.1"
    http_port: int = 443
    smb_port: int = 445
    ftp_port: int = 21
    directory: str = "."
    username: str = ""
    password: str = ""
    server_type: str = ""
    read_only: bool = False
    smb_share: str = "EXEGOL"

    # Attribute -> key in the goshs JSON config. Used in both directions
    # (from_json / apply_to), so reading and writing can't drift apart.
    JSON_KEYS: ClassVar[dict[str, str]] = {
        "interface": "interface",
        "http_port": "port",
        "smb_port": "smb_port",
        "ftp_port": "ftp_port",
        "directory": "directory",
        "username": "auth_username",
        "password": "auth_password",
        "read_only": "read_only",
        "smb_share": "smb_share",
    }

    # Defaults used when a key is missing from a profile, where they differ
    # from the dataclass defaults above.
    PROFILE_DEFAULTS: ClassVar[dict[str, object]] = {"directory": "/workspace/web"}

    @classmethod
    def from_json(cls, data: dict) -> "ConfigGoshs":
        """Build a config from a goshs JSON profile (missing keys get defaults)."""
        values = {}
        for attr, key in cls.JSON_KEYS.items():
            default = cls.PROFILE_DEFAULTS.get(attr, cls.__dataclass_fields__[attr].default)
            values[attr] = data.get(key, default)

        if data.get("smb_server", False):
            values["server_type"] = "SMB"
        elif data.get("ftp", False):
            values["server_type"] = "FTP"
        else:
            values["server_type"] = "HTTPS"

        return cls(**values)

    @classmethod
    def from_file(cls, config_filename: str) -> "ConfigGoshs":
        """Load a profile from the config folder (~/.webserver_tui)."""
        with open(CONFIG_FOLDER / config_filename, "r") as config_file:
            return cls.from_json(json.load(config_file))

    def apply_to(self, data: dict) -> dict:
        """Write this config into a goshs JSON config (modified in place and returned).

        Keys that ConfigGoshs doesn't know about are left untouched.
        """
        for attr, key in self.JSON_KEYS.items():
            data[key] = getattr(self, attr)

        data["smb_server"] = self.server_type == "SMB"
        data["ftp"] = self.server_type == "FTP"
        if self.server_type in ("SMB", "FTP"):
            data["http_server"] = False
        return data
