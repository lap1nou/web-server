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


# Which enum the command id belongs to, per protocol (anything else is HTTP(S)).
DOWNLOADER_TYPES = {"smb": SMBDownloaderType, "ftp": FTPDownloaderType}

# One template per command. Placeholders:
#   {url}       HTTP(S) URL, with user:password@ only when a password is set
#   {ftp_url}   FTP URL, always with user:password@
#   {smb_url}   smb://ip:port/share/path, for smbget
#   {unc}       \\ip\share\path, for Windows
#   {out}       local file name to save as
#   {username}, {password}
#
# References:
# - https://lolbas-project.github.io/#
# - https://github.com/ShutdownRepo/uberfile
COMMAND_TEMPLATES = {
    DownloaderType.CURL: 'curl -k "{url}" -o "{out}"',
    DownloaderType.WGET: 'wget "{url}" -O "{out}"',
    DownloaderType.PYTHON: "python -c \"import urllib.request; urllib.request.urlretrieve('{url}', '{out}')\"",
    DownloaderType.POWERSHELL: 'iwr "{url}" -OutFile "{out}"',
    DownloaderType.BITSADMIN: 'bitsadmin /transfer 1111 /download "{url}" "{out}"',
    DownloaderType.CERTUTIL: 'certutil.exe -urlcache -f "{url}" "{out}"',
    SMBDownloaderType.COPY: 'copy /-Y "{unc}" "{out}"',
    SMBDownloaderType.COPY_ITEM: "Copy-Item '{unc}' '{out}' -Confirm",
    SMBDownloaderType.SMBGET: 'smbget -U "{username}%{password}" "{smb_url}" -o "{out}" ',
    FTPDownloaderType.CURL: 'curl "{ftp_url}" -o "{out}"',
}


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
    command = DOWNLOADER_TYPES.get(protocol, DownloaderType)(command_id)

    path = quote(filename, safe="/")
    credentials = f"{quote(username, safe='')}:{quote(password, safe='')}@"
    base = f"{protocol}://{ip}:{port}"

    return COMMAND_TEMPLATES.get(command, "").format(
        url=f"{protocol}://{credentials if password else ''}{ip}:{port}/{path}",
        ftp_url=f"{protocol}://{credentials}{ip}:{port}/{path}",
        smb_url=f"{base}/{quote(smb_share)}/{path}",
        unc="\\\\" + ip + "\\" + smb_share + "\\" + filename.replace("/", "\\"),
        out=PurePosixPath(filename).name,
        username=username,
        password=password,
    )


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
