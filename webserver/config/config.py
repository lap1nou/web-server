from pathlib import Path
import shutil
import tomllib


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
