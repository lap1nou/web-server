import json
import os
import tempfile
import threading
import queue
import subprocess
from web_server.config.config import ConfigGoshs
from web_server.tui.utils import get_network_interfaces


class GoshsServer:
    def __init__(self, config: ConfigGoshs = None, og_config_file = None):
        self.config = config
        self.og_config_file = og_config_file
        self.tmp_config_file = None
        self.logs = queue.Queue()
        self.thread = threading.Thread(target=self.worker)

    def worker(self):
        command_line = ["goshs"]

        with open(self.og_config_file, "r") as og:
            goshs_tmp = json.load(og)
            goshs_tmp['interface'] = self.config.interface
            goshs_tmp['auth_password'] = self.config.password
            goshs_tmp['port'] = self.config.http_port
            goshs_tmp['directory'] = self.config.directory
            goshs_tmp['read_only'] = self.config.read_only

            if self.config.server_type == "FTP":
                goshs_tmp['ftp'] = True
                goshs_tmp['smb_server'] = False
            elif self.config.server_type == "SMB":
                goshs_tmp['smb_server'] = True
                goshs_tmp['ftp'] = False
            else:
                goshs_tmp['smb_server'] = False
                goshs_tmp['ftp'] = False

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
            self.logs.put(line)

    def start(self):
        self.thread.start()

    def stop(self):
        if self.process:
            self.process.terminate()

        self.thread.join()

        if self.config_file and os.path.exists(self.config_file):
            os.remove(self.config_file)
