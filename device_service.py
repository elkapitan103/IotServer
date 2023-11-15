from flask import jsonify, current_app, render_template
from flask_bcrypt import Bcrypt
from bleak import BleakScanner, BleakClient, BleakError
from sqlalchemy.exc import SQLAlchemyError
from zeroconf import ServiceListener
from datetime import timedelta
import threading
import redis
import re
import logging
from uuid import UUID

from background_tasks import start_background_discovery_task
from models import DeviceMetadata
from database import Session as db, db_session_scope
from db_service import add_to_db, handle_db_error
import config

bcrypt = Bcrypt()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
listener = ServiceListener()

logger.setLevel(config.LOGGING_LEVEL)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.setex("some_token_key", timedelta(minutes=30), "token_value")


def get_redis_connection():
    return redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

# Usage
r = get_redis_connection()
r.setex("some_token_key", timedelta(minutes=30), "token_value")

def validate_device(device):
    """
    Validate the device before storing it.
    :param device: The device object to validate.
    :return: Boolean indicating if the device is valid.
    """
    # Example validation criteria
    return device.name is not None and device.address is not None


def is_valid_mac_address(mac_address):
    """
    Validate the format of a MAC address.
    :param mac_address: The MAC address to validate.
    :return: Boolean indicating if the MAC address is valid.
    """
    mac_regex = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_regex.match(mac_address))

def is_valid_device_name(device_name):
    return 0 < len(device_name) <= 100

def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=4)
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400
    return str(uuid_obj) == uuid_to_test

def add_new_device(name, address, device_type):
    """
    Add a new device to the database.
    :param name: The name of the device.
    :param address: The BLE address of the device.
    :param device_type: The type of the device.
    """
    new_device = DeviceMetadata(name=name, address=address, device_type=device_type)
    with db_session_scope() as session:
        session.add(new_device)
        session.commit()  # Ensure the commit is called to save the record.

async def consolidated_device_discovery(selected_mac_address=None):
    try:
        devices = await BleakScanner.discover()
        with db_session_scope() as session:
            for device in devices:
                if not validate_device(device):
                    continue
                existing_device = session.query(DeviceMetadata).filter_by(address=device.address).first()
                if not existing_device:
                    new_device = DeviceMetadata(address=device.address, name=device.name)
                    session.add(new_device)
                    if selected_mac_address and device.address == selected_mac_address:
                        new_device.is_gateway = True
                        current_app.logger.info(f"Discovered gateway device: {device.address}")
                    else:
                        current_app.logger.info(f"Discovered device: {device.address}")
        current_app.logger.info(f"Total devices discovered: {len(devices)}")
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error during device discovery: {e}")
        return handle_db_error(e)
    except Exception as e:
        current_app.logger.error(f"Unexpected error during device discovery: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    
def discover_services():
    try:
        discovery_thread = threading.Thread(target=start_background_discovery_task, args=(current_app,))
        discovery_thread.daemon = True
        discovery_thread.start()
        return listener.available_devices
    except Exception as e:
        logger.error(f"Error in discover_services: {e}")
        return jsonify({"error": "Failed to discover services"}), 500

async def scan_bluetooth_devices(duration=10):
    try:
        devices = await BleakScanner.discover(timeout=duration)
        devices_data = [
            {"address": device.address, "name": device.name} for device in devices
        ]
        return devices_data
    except BleakError as e:
        current_app.logger.error(f"BLE error: {e}")
        return jsonify({"error": "Failed to interact with BLE device"}), 500

async def get_all_characteristics():
    try:
        async with BleakClient(current_app.config["GATEWAY_MAC_ADDRESS"]) as client:
            if client.is_connected:
                logger.info("Successfully connected to the IoT Gateway.")
                services = await client.get_services()
                characteristics = []
                for service in services:
                    for characteristic in service.characteristics:
                        characteristics.append(str(characteristic.uuid))
                return characteristics
            else:
                logger.error("Failed to connect to the IoT Gateway.")
                return []
    except Exception as e:  
        logger.error(f"Error: BLE operation failed: {e}")
        return jsonify({"error": "BLE operation failed"}), 500
    
async def scan_nearby_ble_devices():
    try:
        return await scan_bluetooth_devices()
    except BleakError as e:
        logger.error(f"BLE error: {e}")
        return None

async def discover_ble_characteristics():
    try:
        return await get_all_characteristics()
    except BleakError as e:
        logger.error(f"BLE error: {e}")
        return None

def discover_ble_devices():
    try:
        return scan_bluetooth_devices()
    except Exception as e:
        logger.error(f"Error during BLE device discovery: {e}")
        return []
    
def store_device(device):
    """
    Store the device in the database if it doesn't exist.
    :param device: The device object to store.
    :return: Boolean indicating success or failure.
    """
    try:
        with db_session_scope() as session:
            existing_device = session.query(DeviceMetadata).filter_by(address=device.address).first()
            if not existing_device:
                new_device = DeviceMetadata(address=device.address, name=device.name, is_gateway=device.is_gateway)
                session.add(new_device)
                session.commit()
                logger.info(f"Successfully added device with MAC: {new_device.mac_address} to database.")
                return True
            else:
                logger.info(f"Device with MAC: {device.address} already exists in database.")
                return False
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"General error: {e}")
        return False


def device_exists(mac_address):
    """Check if a device with the given MAC address exists in the database."""
    try:
        with db_session_scope() as session:
            existing_device = session.query(DeviceMetadata).filter_by(address=mac_address).first()
            return bool(existing_device)
    except Exception as e:
        logger.error(f"Error while fetching device by MAC address {mac_address}: {e}")
        return None

async def select_ble_device(device_name, mac_address):
    if not is_valid_mac_address(mac_address) or not is_valid_device_name(device_name):
        return False, "Invalid MAC address or device name"
    try:
        async with BleakClient(mac_address) as client:
            await client.connect()
            if client.is_connected:
                return True, "Device selected successfully"
            else:
                return False, "Failed to connect to the device"
    except BleakError as e:
        return False, f"BLE error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def discover_and_store():
    """
    Discover devices and store them in the database.
    :return: Tuple indicating success or failure and a message.
    """
    try:
        discovered_devices = discover_services()
        for device in discovered_devices:
            if validate_device(device):
                store_device(device)
        return True, "Devices discovered and stored successfully"
    except Exception as e:
        logger.error(f"Error during device discovery: {str(e)}")
        return False, f"Error during device discovery: {str(e)}"
