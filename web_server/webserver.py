from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import queue


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        message = format % args
        self.server.logs.put(
            f"{self.address_string()} - - [{self.log_date_time_string()}] {message}"
        )


class WebServer:
    def __init__(
        self, host: str = "localhost", port: int = 8080, directory: str = None
    ):
        def handler(*args, **kwargs):
            return CustomHTTPRequestHandler(*args, directory=directory, **kwargs)

        self.server = ThreadingHTTPServer((host, port), handler)
        self.server.logs = queue.Queue()
        self.thread = threading.Thread(target=self.server.serve_forever)

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
