from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
import logging
import services 
from data_ops import fetch_process_and_store_data

logger = logging.getLogger(__name__)

def validate_discovered_device(device):
    # This is just a generic example. Adjust based on your actual device structure and requirements.
    if not device or not hasattr(device, 'address') or not hasattr(device, 'is_gateway'):
        return False
    return True

def schedule_data_collection():
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(fetch_process_and_store_data, "interval", minutes=1)  # Fixed the function reference
        scheduler.start()
    except Exception as e:
        logger.error(f"Error during scheduling data collection: {e}")

def start_background_discovery_task(selected_mac_address):
    try:
        devices = services.scan_bluetooth_devices()
        for device in devices:
            if not validate_discovered_device(device):
                logger.warning(f"Invalid device structure for MAC: {device.mac_address if device else 'Unknown'}")
                continue

            if device.address == selected_mac_address:
                device.is_gateway = True
                current_app.logger.info(f"Discovered gateway device: {device.address}")
            else:
                current_app.logger.info(f"Discovered device: {device.address}")

            if not services.device_exists(device.address):
                if not services.store_discovered_device(device):
                    logger.error(f"Failed to store device with MAC: {device.mac_address} to database.")
    except Exception as e:
        current_app.logger.error(f"Error during background discovery: {e}")

def background_task_with_context(mac_address):
    with current_app.app_context():
        services.consolidated_device_discovery(mac_address)
