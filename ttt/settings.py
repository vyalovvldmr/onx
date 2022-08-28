import logging
import os


# SERVER_IP = "vyalovvldmr-ttt.herokuapp.com"
SERVER_IP = "0.0.0.0"
SERVER_PORT = int(os.environ.get('PORT', 8080))

LOGGING_LEVEL = logging.DEBUG

CLIENT_RECONNECT_TIMEOUT = 1

DEFAULT_GRID_SIZE = 3

DEFAULT_WINNING_LENGTH = 3
