import sys
import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

stdoutHandler = logging.StreamHandler(stream=sys.stdout)

file_path = os.path.abspath(os.path.dirname(__file__))
fileHandler = RotatingFileHandler(f"{file_path}/../logs.txt", backupCount=5, maxBytes=5000000)

fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s%(lineno)s | %(process)d >>> %(message)s"
)

stdoutHandler.setFormatter(fmt)
fileHandler.setFormatter(fmt)

logger.addHandler(stdoutHandler)
logger.addHandler(fileHandler)

logger.setLevel(logging.INFO)