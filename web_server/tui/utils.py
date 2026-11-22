import ipaddress
import platform
import subprocess
from enum import Enum
from pathlib import Path, PurePosixPath
from socket import AddressFamily
from urllib.parse import quote

import psutil
import pyperclip

MIN_PORT = 1
MAX_PORT = 65535


class DownloaderType(Enum):
    CURL = 1
    WGET = 2
    PYTHON = 3
    POWERSHELL = 4
    BITSADMIN = 5
    CERTUTIL = 6


class SMBDownloaderType(Enum):
    COPY = 1
    COPY_ITEM = 2
    SMBGET = 3


class FTPDownloaderType(Enum):
    CURL = 1


class IPFormat(Enum):
    DECIMAL = 1
    OCTAL = 2
    HEX = 3
    DOTTED_HEX = 4
    DOTTED_OCTAL = 5


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
    command_id: int,
    protocol: str,
    ip: str,
    port: int,
    username: str,
    password: str,
    filename: str,
    smb_share: str,
) -> str:
    target_path = PurePosixPath(filename).name

    if password:
        url = f"{protocol}://{quote(username, safe='')}:{quote(password, safe='')}@{ip}:{port}/{quote(filename, safe='/')}"
    else:
        url = f"{protocol}://{ip}:{port}/{quote(filename, safe='/')}"

    if protocol == "smb":
        command_id = SMBDownloaderType(command_id)
    elif protocol == "ftp":
        command_id = FTPDownloaderType(command_id)
    else:
        command_id = DownloaderType(command_id)

    if isinstance(command_id, DownloaderType):
        if command_id == DownloaderType.CURL:
            return f'''curl "{url}" -o "{target_path}"'''
        elif command_id == DownloaderType.WGET:
            return f'''wget "{url}" -O "{target_path}"'''
        elif command_id == DownloaderType.PYTHON:
            return f'''python -c "import urllib.request; urllib.request.urlretrieve('{url}', '{target_path}')"'''
        elif command_id == DownloaderType.POWERSHELL:
            return f'''iwr "{url}" -OutFile "{target_path}"'''
        elif command_id == DownloaderType.BITSADMIN:
            return f'''bitsadmin /transfer 1111 /download "{url}" "{target_path}"'''
        elif command_id == DownloaderType.CERTUTIL:
            return f'''certutil.exe -urlcache -f "{url}" "{target_path}"'''
        else:
            return ""
    elif isinstance(command_id, SMBDownloaderType):
        if command_id == SMBDownloaderType.COPY:
            unc = "\\\\" + ip + "\\" + smb_share + "\\" + filename.replace("/", "\\")
            return f'''copy /-Y "{unc}" "{target_path}"'''
        elif command_id == SMBDownloaderType.COPY_ITEM:
            unc = "\\\\" + ip + "\\" + smb_share + "\\" + filename.replace("/", "\\")
            return f"""Copy-Item '{unc}' '{target_path}' -Confirm"""
        elif command_id == SMBDownloaderType.SMBGET:
            return f'''smbget -U "{username}%{password}" "{protocol}://{ip}:{port}/{quote(smb_share)}/{quote(filename, safe="/")}" -o "{target_path}" '''
    elif isinstance(command_id, FTPDownloaderType):
        return f'''curl "{protocol}://{quote(username, safe="")}:{quote(password, safe="")}@{ip}:{port}/{quote(filename, safe="/")}" -o "{target_path}"'''
    else:
        return ""


def get_files_list(root: str, search: str = "*"):
    files = []

    # When Python 3.12 available, use case_sensitive=False
    for path in Path(root).rglob(search, case_sensitive=False):
        if path.is_file() and ".git" not in path.parts:
            files.append(str(path.relative_to(root)))

    return files


def get_network_interfaces() -> dict[str, str]:
    interfaces = {}

    for interface_name, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == AddressFamily.AF_INET:
                interfaces[interface_name] = address.address

    interfaces["all"] = "0.0.0.0"

    return interfaces


def ip_formats(ip: str, ip_format: IPFormat = None) -> str:
    if not ip_format:
        return ip

    n = int(ipaddress.IPv4Address(ip))  # validates and gives a 32-bit int
    octets = ip.split(".")

    if ip_format == IPFormat.DECIMAL:
        result = str(n)
    elif ip_format == IPFormat.OCTAL:
        result = "0" + format(n, "o")
    elif ip_format == IPFormat.HEX:
        result = hex(n)
    elif ip_format == IPFormat.DOTTED_OCTAL:
        result = ".".join(f"0{int(o):o}" for o in octets)
    elif ip_format == IPFormat.DOTTED_HEX:
        result = ".".join(f"0x{int(o):02x}" for o in octets)

    return result
