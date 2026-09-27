import os

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))
HOST = os.getenv("VALIDATOR_HOST", "0.0.0.0")
PORT = int(os.getenv("VALIDATOR_PORT", 8001))
