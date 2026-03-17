from enum import Enum
from pathlib import Path
from socket import AddressFamily
import pyperclip
import subprocess
import platform
import psutil


class DownloaderType(Enum):
    CURL = 1
    WGET = 2
    PYTHON = 3
    POWERSHELL = 4
    BITSADMIN = 5
    CERTUTIL = 6


class ServerType(Enum):
    WEBSERVER = "webserver"
    UPDOG = "updog"
    GOSHS = "goshs"


def copy_in_clipboard(input: str):
    # Reference:
    # https://stackoverflow.com/questions/48499398/how-to-run-a-process-and-quit-after-the-script-is-over
    # https://github.com/kovidgoyal/kitty/issues/828

    # Pyperclip doesn't seems to provide public
    # API access to the primary argument
    # so we must manually do it
    if platform.system() == "Linux":
        subprocess.run(
            ["xclip", "-selection", "primary"],
            input=input.encode("utf-8"),
            stdout=subprocess.DEVNULL,
        )

    pyperclip.copy(input)


# References:
# - https://lolbas-project.github.io/#
# - https://github.com/ShutdownRepo/uberfile
def generate_download_command(
    command_id: DownloaderType, address: str, target_path: str
) -> str:
    target_path = Path(target_path)

    if command_id == DownloaderType.CURL:
        return f'''curl "{address}" -o "{target_path.name}"'''
    elif command_id == DownloaderType.WGET:
        return f'''wget "{address}" -O "{target_path.name}"'''
    elif command_id == DownloaderType.PYTHON:
        return f'''python -c "import urllib.request; urllib.request.urlretrieve('{address}', '{target_path.name}')"'''
    elif command_id == DownloaderType.POWERSHELL:
        return f'''iwr "{address}" -OutFile "{target_path.name}"'''
    elif command_id == DownloaderType.BITSADMIN:
        return (
            f'''bitsadmin /transfer 1111 /download "{address}" "{target_path.name}"'''
        )
    elif command_id == DownloaderType.CERTUTIL:
        return f'''certutil.exe -urlcache -f "{address}" "{target_path.name}"'''
    else:
        return ""


def get_files_list(root: str, search: str = "*"):
    files = []

    # When Python 3.12 available, use case_sensitive=False
    for path in Path(root).rglob(search, case_sensitive=False):
        if path.is_file() and ".git" not in path.parts:
            files.append(str(path.relative_to(root)))

    return files


def get_network_interfaces() -> list[tuple[str, str]]:
    interfaces = []

    for interface_name, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == AddressFamily.AF_INET:
                interfaces.append((interface_name, address.address))

    interfaces.append(("all", "0.0.0.0"))

    return interfaces


def find_interface_by_name(interface_name: str) -> str:
    for interface in get_network_interfaces():
        if interface_name == interface[0]:
            return interface


def find_interface_by_ip(interface_ip: str) -> str:
    for interface in get_network_interfaces():
        if interface_ip == interface[1]:
            return interface
