from data_helpers import data_queue, MAX_QUEUE_SIZE
from zeroconf import Zeroconf, ServiceBrowser
import requests
from bleak import BleakScanner, BleakClient
import bleak
import asyncio
import time
import logging
import signal

zeroconf = None
listener = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyListener:
    def remove_service(self, zeroconf, type, name, service):
        logger.info(f"Service {name} removed")
        try:
            if data_queue.qsize() < MAX_QUEUE_SIZE:
                data_queue.put(name)
            else:
                logging.warning("Data queue is full. Consider processing data or increasing queue size.")
        except Exception as e:
            logging.error(f"Error during discovery: {e}")

    def add_service(self, zeroconf, type, name, service):
        logger.info(f"Service {name} added")
        try:
            # Validate that the service provides the necessary details
            if not all(attr in dir(service) for attr in ['address', 'port']):
                raise ValueError(f"Service {name} lacks required details.")
            device_ip = service.address
            device_port = service.port
            # Fetch data from the device (hypothetical endpoint)
            response = requests.get(f"http://{device_ip}:{device_port}/data_endpoint")
            if response.status_code == 200:
                data = response.json()
                data_queue.put(data)
            else:
                logging.warning(f"Failed to fetch data from device {name}")
        except Exception as e:
            logging.error(f"Error during discovery: {e}")

    def update_service(self, zeroconf, type, name, service):
        logger.info(f"Service {name} updated")

def initialize_discovery():
    global zeroconf, listener
    if not zeroconf and not listener:
        zeroconf = Zeroconf()
        listener = MyListener()
        logger.info("Zeroconf and listener initialized.")

def start_discovery():
    global zeroconf, listener
    if not zeroconf or not listener:
        initialize_discovery()
    browser = ServiceBrowser(zeroconf, "_ble_device._tcp.local.", listener)
    logger.info("Started device discovery...")

def stop_discovery():
    global zeroconf
    if zeroconf:
        zeroconf.close()
        logger.info("Stopped device discovery...")

def discover_devices(duration=10):
    global zeroconf, listener
    if not zeroconf or not listener:
        logger.error("Zeroconf or listener not initialized.")
        return
    try:
        logging.info("Starting device discovery...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(1)
        zeroconf.close()
        logger.info("Device discovery stopped.")
    except Exception as e:
        logging.error(f"Error during device discovery: {e}")

async def get_discovered_data():
    try:
        device_address = "TARGET_MAC_ADDRESS"
        characteristic_uuid = "CHARACTERISTIC_UUID"
        async with BleakClient(device_address) as client:
            if not client.is_connected:
                raise ConnectionError("Failed to connect to the BLE device.")
            raw_data = await client.read_gatt_char(characteristic_uuid)
            # Validate raw data
            if len(raw_data) < 2:
                raise ValueError("Unexpected data format or length.")
            temperature = raw_data[0]
            humidity = raw_data[1]
            return {
                "temperature": temperature,
                "humidity": humidity
            }
    except Exception as e:
        logging.error(f"Error fetching discovered data: {e}")
        return None

def graceful_shutdown(signum, frame):
    logger.info("Gracefully shutting down...")
    loop = asyncio.get_event_loop()
    loop.stop()

async def discover_services_and_characteristics():
    try:
        # Callback for discovered devices
        def discovery_callback(device, advertisement_data):
            logger.info(f"Discovered {device.name} ({device.address})")
        scanner = BleakScanner(detection_callback=discovery_callback)
        await scanner.start()
        await asyncio.sleep(5)
        await scanner.stop()
        devices = scanner.discovered_devices
        for device in devices:
            MAX_RETRIES = 3
            for retry in range(MAX_RETRIES):
                try:
                    async with BleakClient(device) as client:
                        services = client.services
                        for service in services:
                            logger.info(f"Service: {service.uuid}")
                            for char in service.characteristics:
                                logger.info(f"  Characteristic: {char.uuid}")
                except bleak.exc.BleakError as e:
                    if retry < MAX_RETRIES - 1:
                        logger.warning(f"Connection failed. Retrying ({retry + 1}/{MAX_RETRIES})...")
                    else:
                        logger.warning(f"Failed to connect after {MAX_RETRIES} attempts.")
                        break
    except bleak.exc.BleakError as e:
        logger.error(f"BleakError encountered: {e}")

def handle_asyncio_exception(loop, context):
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")

loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_asyncio_exception)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

if __name__ == "__main__":
    try:
        asyncio.run(discover_services_and_characteristics())
    except Exception as e:
        logger.error(f"Error during service and characteristic discovery: {e}")

