from web_server.config.config import AppConfig
from web_server.tui.tui import TUI
from web_server.cli.arguments import parse_arguments


def main():
    args = parse_arguments().parse_args()
    config = AppConfig().config
    TUI(args, config).run()
