import argparse


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="web-server",
        description="""
            Web-server: A cool tool.
        """,
    )
    parser.add_argument(
        "-d", "--directory", help="The directory to serve files from.", required=True
    )
    parser.add_argument("-p", "--port", help="The port of the webserver.", default=8080)
    parser.add_argument(
        "-i", "--interface", help="The interface where the webserver will listen."
    )

    return parser
