
import logging
import asyncio

from models import SensorData
from data_ops import connect_to_gateway
from database import Session as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_sensor_data(temperature, humidity):
    if not (-50 <= temperature <= 50):
        raise ValueError(f"Invalid temperature value: {temperature}")
    if not (0 <= humidity <= 100):
        raise ValueError(f"Invalid humidity value: {humidity}")

def validate_data(data):
    if data is None:
        logger.warning("Received data is None")
        return False
    if "error" in data:
        logger.error(f"Error in received data: {data['error']}")
        return False
    if "temperature" not in data or not (0 <= data["temperature"] <= 100):
        logger.warning("Invalid temperature value in received data")
        return False
    if "humidity" not in data or not (0 <= data["humidity"] <= 100):
        logger.warning("Invalid humidity value in received data")
        return False
    return True

def add_new_device_record(temperature, humidity):
    with db() as session:
        new_record = SensorData(temperature=temperature, humidity=humidity)
        session.add(new_record)
        
def fetch_all_sensor_data():
    with db() as session:
        return session.query(SensorData).all()
    
def fetch_filtered_sensor_data(start_time, end_time):
    return SensorData.query.filter(SensorData.timestamp.between(start_time, end_time)).all()

def get_sensor_data():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(connect_to_gateway())