import threading
import queue
import subprocess
from web_server.config.config import ConfigGoshs


class GoshsServer:
    def __init__(self, config: ConfigGoshs = None):
        self.config_file = config.config_file
        self.logs = queue.Queue()
        self.thread = threading.Thread(target=self.worker)

    def worker(self):
        command_line = ["goshs"]

        if self.config_file:
            command_line.extend(["-C", self.config_file])

        self.process = subprocess.Popen(
            command_line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in self.process.stdout:
            self.logs.put(line)

    def start(self):
        self.thread.start()

    def stop(self):
        if self.process:
            self.process.terminate()

        self.thread.join()
