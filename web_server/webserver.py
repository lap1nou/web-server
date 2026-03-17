from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import queue
from web_server.config.config import ConfigServer


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        message = format % args
        self.server.logs.put(
            f"{self.address_string()} - - [{self.log_date_time_string()}] {message}"
        )


class WebServer:
    def __init__(self, config: ConfigServer = None):
        def handler(*args, **kwargs):
            return CustomHTTPRequestHandler(*args, directory=config.directory, **kwargs)

        self.server = ThreadingHTTPServer((config.interface[1], config.port), handler)
        self.server.logs = queue.Queue()
        self.thread = threading.Thread(target=self.server.serve_forever)

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
