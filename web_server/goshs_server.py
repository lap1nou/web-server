import collections
import json
import os
import subprocess
import tempfile
import threading

from web_server.config.config import ConfigGoshs


class GoshsServer:
    def __init__(self, config: ConfigGoshs = None, og_config_file=None):
        self.config = config
        self.og_config_file = og_config_file
        self.tmp_config_file = None
        self.logs = collections.deque(maxlen=5000)
        self.logs_lock = threading.Lock()
        self.thread = threading.Thread(target=self.worker)

    def worker(self):
        command_line = ["goshs"]

        with open(self.og_config_file, "r") as og:
            goshs_tmp = self.config.apply_to(json.load(og))

        if self.config:
            with tempfile.NamedTemporaryFile(
                "w", prefix="goshs_", suffix=".json", delete=False
            ) as config_file:
                json.dump(goshs_tmp, config_file)
                command_line.extend(["-C", config_file.name])
                self.config_file = config_file.name

        self.process = subprocess.Popen(
            command_line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in self.process.stdout:
            with self.logs_lock:
                self.logs.append(line)

    def get_logs(self) -> list[str]:
        with self.logs_lock:
            return list(self.logs)

    def start(self):
        self.thread.start()

    def stop(self):
        if self.process:
            self.process.terminate()

        self.thread.join()

        if self.config_file and os.path.exists(self.config_file):
            os.remove(self.config_file)
