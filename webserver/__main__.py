from webserver.config.config import AppConfig
from webserver.tui.tui import TUI
from webserver.cli.arguments import parse_arguments


def main():
    args = parse_arguments().parse_args()
    config = AppConfig().config
    TUI(args, config).run()
