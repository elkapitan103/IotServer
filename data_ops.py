from database import db_session_scope
from models import SensorData
from utils import is_data_valid
from data_helpers import extract_data, process_data, data_queue
from config import CELERY_BROKER_URL
from __init__ import create_app

import logging
import threading
from bleak import BleakScanner, BleakClient
from datetime import datetime
import queue
import asyncio
from flask import current_app

# This decorator will allow asynchronous functions to be called inside Flask routes.
from flask import copy_current_request_context
from celery import Celery

db_write_lock = threading.Lock()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = create_app()

celery_app = Celery('data_ops', broker=CELERY_BROKER_URL)  # Use the imported broker URL

def extract_data_from_queue():
    try:
        data = data_queue.get(timeout=10)
        logger.info("Data successfully extracted from the queue.")
    except queue.Empty:
        logging.warning("Queue is empty. No data to process.")
        return None
    except Exception as e:
        logging.error(f"Error during data extraction: {e}")
        return None
    return data

def store_data(data):
    with db_write_lock:
        logger.info(f"Storing data: {data}")
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
            temperature = data["temperature"]
            humidity = data["humidity"]
            record = SensorData(timestamp=timestamp, temperature=temperature, humidity=humidity)
            with db_session_scope() as session:  # Using the context manager
                session.add(record)
            logger.info("Data has been stored successfully!")
        except Exception as e:
            logger.error(f"Error storing data: {e}")

async def connect_to_device(device):
    with app.app_context():
        characteristic_uuid = current_app.config.get('CHARACTERISTIC_UUID')
        try:
            client = BleakClient(device.address)
            await client.connect()
            if not client.is_connected:
                logger.error("Failed to connect to the device!")
                return {"status": "failure", "error": "Failed to connect"}
            data = await client.read_gatt_char(characteristic_uuid)
            if not is_data_valid(data):  # Assuming this function returns a boolean
                logger.warning("Received invalid data from the device.")
                return {"status": "failure", "error": "Invalid data received"}
            await client.disconnect()
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            return {"status": "failure", "error": str(e)}
        
async def scan_device():
    with app.app_context():
        try:
            return [device.name for device in await BleakScanner.discover() if device.name]
        except Exception as e:
            logger.error(f"Error occurred during device scanning: {e}", exc_info=True)
            return []

async def connect_to_gateway():
    with app.app_context():
        retries = 3
        target_name = current_app.config.get('DEVICE_NAME')
        target_mac_address = current_app.config.get('TARGET_MAC_ADDRESS')
        while retries:
            devices = await BleakScanner.discover()
            try:
                if target_name and target_mac_address:
                    client = BleakClient(target_mac_address)
                    if client.is_connected:
                        logger.info(f"Connected to device: {target_name} with MAC: {target_mac_address}")
                        return client
                    else:
                        logger.warning(f"Failed to connect to device: {target_name}. Falling back to dynamic discovery.")
                selected_gateway = next((device for device in devices if "IoT_Gateway" in device.name), None)
                if not selected_gateway:
                    retries -= 1
                    logger.error("No IoT_Gateway devices found. Retrying...")
                    await asyncio.sleep(60)
                    continue
                client = BleakClient(selected_gateway.address)
                await client.connect()
                logger.info(f"Connected to gateway: {selected_gateway.name} with MAC: {selected_gateway.address}")
                return client
            except Exception as e:
                retries -= 1
                logger.error(f"Error during gateway connection: {e}")
                await asyncio.sleep(60)
        logger.error("Max retries reached. Aborting connection attempt.")
        return None

async def discover_devices():
    return await BleakScanner.discover()

devices = asyncio.run(discover_devices())

async def main_async_operations():
    with app.app_context():
        devices = await discover_devices()
        if not devices:
            logger.error("No devices found.")
            return
        target_name = current_app.config.get('DEVICE_NAME')
        target_mac_address = current_app.config.get('TARGET_MAC_ADDRESS')
        device = next((d for d in devices if target_name in d.name and target_mac_address in d.address), None)
        if device:
            await connect_to_device(device)
            await scan_device()
            await connect_to_gateway()
        else:
            logger.warning("Target device not found!")

@Celery.task
@copy_current_request_context
def fetch_process_and_store_data():
    try:
        data = connect_to_gateway()
        if not data:
            logger.error("No data received from the gateway.")
            return
        extracted_data = extract_data(data)
        if not is_data_valid(extracted_data):
            logger.error("Received invalid data.")
            return
        processed_data = process_data(extracted_data)
        store_data(processed_data)
        logger.info("Data stored successfully.")
    except Exception as e:
        logger.error(f"Error processing or storing data: {e}")

def main_data_ops():
    with app.app_context():
        raw_data = data_queue.get(timeout=10)
        data = extract_data(raw_data)
        store_data(data)

celery_app = Celery('data_ops', broker='CELERY_BROKER_URL')

@celery_app.task
def store_data_background(data):
    with db_write_lock:
        logger.info(f"Storing data: {data}")
        try:
            timestamp = datetime.fromisoformat(data["timestamp"])
            temperature = data["temperature"]
            humidity = data["humidity"]
            record = SensorData(timestamp=timestamp, temperature=temperature, humidity=humidity)
            with db_session_scope() as session:
                session.add(record)
            logger.info("Data has been stored successfully in the background!")
        except Exception as e:
            logger.error(f"Error storing data: {e}")

if __name__ == "__main__":
    discover_devices()  
    asyncio.run(main_async_operations())
    extract_data_from_queue()




