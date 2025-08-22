import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FORMAT = '%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'app.log'

def setup_logging():
    root_logger = logging.getLogger()
    
    if root_logger.hasHandlers():
        return

    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")