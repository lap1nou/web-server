import threading
import queue
import subprocess
from web_server.config.config import ConfigUpdog


class UpdogServer:
    def __init__(self, config: ConfigUpdog = None):
        self.host = config.host
        self.port = config.port
        self.directory = config.directory
        self.password = config.password
        self.logs = queue.Queue()
        self.thread = threading.Thread(target=self.worker)

    def worker(self):
        command_line = ["updog"]

        if self.host:
            command_line.extend(["-b", self.host])

        if self.directory:
            command_line.extend(["-d", self.directory])

        if self.port:
            command_line.extend(["-p", self.port])

        if self.password:
            command_line.extend(["--password", self.password])

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
