
import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # or get from config
    # ... Set up logging format and handlers ...
    return logger

# In services.py
from logger import setup_logger
logger = setup_logger(__name__)

# Example usage
logger.info("Info level log message")
logger.error("Error level log message")
