from queue import Queue, Empty
import datetime
import logging

logger = logging.getLogger(__name__)
MAX_QUEUE_SIZE = 1000 
data_queue = Queue(MAX_QUEUE_SIZE)

def add_to_queue(data):
    if data_queue.qsize() < MAX_QUEUE_SIZE:
        data_queue.put(data)
    else:
        logger.warning("Data queue is full. Consider processing data or increasing queue size.")

def get_from_queue():
    try:
        data = data_queue.get_nowait()
        return data
    except Empty:
        logger.warning("Data queue is empty.")
        return None

def extract_data(raw_data):
    try:
        temperature = raw_data.get("temperature", 25.0)
        humidity = raw_data.get("humidity", 60.0)

        data = {
            "timestamp": datetime.datetime.now().isoformat(),  # added datetime. before now()
            "temperature": temperature,
            "humidity": humidity
        }
        return data
    except Exception as e:
        logger.error(f"Data extraction failed: {e}")
        return None

def process_data(data):
    if not validate_data(data):
        logger.error("Invalid data provided.")
        return
    if "value" in data:
        data["value"] = data["value"] / 100  
    logger.info(f"Processing data: {data}")
    return data

def validate_data(data):
    if not data:
        return False
    # Add more validation checks as needed
    # For example, ensure 'value' is a number
    if "value" in data and not isinstance(data["value"], (int, float)):
        return False
    return True
