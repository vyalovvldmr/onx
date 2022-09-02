import logging
import os

SERVER_HOST = os.environ.get("LOCALHOST", "vyalovvldmr-onx.herokuapp.com")

SERVER_PORT = int(os.environ.get("PORT", 80))

LOGGING_LEVEL = logging.DEBUG

WS_HEARTBEAT_TIMEOUT = 10

CLIENT_RECONNECT_TIMEOUT = 1

DEFAULT_GRID_SIZE = 3

DEFAULT_WINNING_LENGTH = 3
