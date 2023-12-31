from flask import Blueprint, jsonify, render_template, request, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from bleak import BleakClient, BleakError
from bokeh.embed import components
from bokeh.resources import CDN
from datetime import datetime
from threading import Thread
import asyncio
import logging

from models import SensorData, DeviceMetadata
from visualization import create_bar_chart
from data_ops import extract_data_from_queue
from database import Session as db
import services
import background_tasks

api = Blueprint('api', __name__)

device_name, status, last_activity = services.fetch_request_data()
status_response = services.validate_status(status)
parsed_activity_response = services.parse_last_activity(last_activity)

logger = logging.getLogger(__name__)

def log_error(context, error):
    logger.error(f"{context} - Error: {error}", exc_info=True)

def api_response(success, data=None, message=None, error=None, status_code=200):
    if success:
        return jsonify({"success": True, "data": data, "message": message}), status_code
    else:
        return jsonify({"success": False, "error": error}), status_code

@api.route("/scan", methods=["GET"])
def scan_for_bluetooth_devices():
    """
    Scan for nearby Bluetooth devices and return a list of discovered devices.
    """
    devices = services.scan_nearby_ble_devices()
    if devices:
        return render_template("select_device.html", devices=devices)
    else:
        return api_response({"error": "Failed to interact with BLE device"}), 500

@api.route("/select_device", methods=["POST"])
@jwt_required()
def select_device():
    selected_device_name = request.form.get('device_name')
    selected_mac_address = request.form.get('mac_address')
    success, message = services.select_ble_device(selected_device_name, selected_mac_address)
    if success:
        return api_response({"message": message}), 200
    else:
        return api_response({"error": message}), 400

@api.route("/discover_characteristics", methods=["GET"])
def discover_characteristics():
    characteristics = services.discover_ble_characteristics()
    if characteristics:
        return render_template("select_characteristic.html", characteristics=characteristics)
    else:
        return api_response({"error": "Failed to interact with BLE device"}), 500

@api.route("/select_characteristic", methods=["POST"])
@jwt_required()
def select_characteristic():
    characteristic_uuid = request.form.get('characteristic_uuid')
    if not characteristic_uuid or not services.is_valid_uuid(characteristic_uuid):
        return api_response({"error": "Invalid or missing UUID"}), 400
    try:     
        current_app.config['CHARACTERISTIC_UUID'] = characteristic_uuid  
        available_characteristics = asyncio.run(services.get_all_characteristics())
        if not characteristic_uuid:
            return "Characteristic UUID is required", 400
        if characteristic_uuid not in available_characteristics:
            logger.error(f"Invalid UUID selected: {characteristic_uuid}")
            return "Invalid characteristic selected!", 400
        current_app.config["CHARACTERISTIC_UUID"] = characteristic_uuid
        logger.info(f"Selected characteristic UUID: {characteristic_uuid}")
        if not services.is_valid_uuid(characteristic_uuid):
            return api_response({"error": "Invalid UUID format"}), 400
        return "Characteristic selected successfully!", 200
    except BleakError as e:
        log_error(f"BLE error: {e}")
        return api_response({"error": "Failed to interact with BLE device"}), 500

@api.route("/chart", methods=["GET"])
@jwt_required()
def get_chart():
    sensor_data = SensorData.query.all()
    data = [
        {
            "timestamp": record.timestamp.isoformat(),
            "temperature": record.temperature,
            "humidity": record.humidity,
        }
        for record in sensor_data
    ]
    plot = create_bar_chart(data, "timestamp", "temperature", "Temperature over Time")
    script, div = components(plot)
    return render_template(
        "chart.html",
        script=script,
        div=div,
        cdn_js=CDN.js_files[0],
        cdn_css=CDN.css_files[0] if CDN.css_files else None,
    )

@api.route('/devices', methods=['GET'])
def get_devices():
    devices = services.fetch_all_devices()
    if devices:
        devices_list = [{"device_name": device.device_name, "status": device.status, "last_activity": device.last_activity} for device in devices]
        return api_response(devices_list)
    else:
        return api_response({"error": "Failed to fetch devices"}), 500

@api.route('/api/discover_and_store_devices')
def discover_and_store_devices():
    success, message = services.discover_and_store()
    if success:
        return api_response({"message": message}), 200
    else:
        return api_response({"error": message}), 500

@api.route('/api/get_device_data/<device_name>', methods=['GET'])
async def get_device_data(device_name):
    timestamp = datetime.now()
    try:     
        data = await services.fetch_device_data(device_name, current_app.config['CHARACTERISTIC_UUID'])
        try:
            device = DeviceMetadata.query.filter_by(name=device_name).first()
            if not device:
                return api_response(success=False, error="Device not found"), 404
            characteristic_uuid = current_app.config['CHARACTERISTIC_UUID']
            data_raw = None
            async with BleakClient(device) as client:
                try:
                    data_raw = await client.read_gatt_char(characteristic_uuid)
                except Exception as e:
                    logger.error(f"Error reading from BLE device: {e}")
                    return api_response(success=False, error=str(e)), 500
            data = extract_data_from_queue(data_raw)
            if not (temperature := data.get('temperature')) or type(temperature) is not float:
                logger.error("Invalid temperature value")
                return api_response(success=False, error="Invalid temperature value"), 400
            if not (humidity := data.get('humidity')) or type(humidity) is not float or not (0 <= humidity <= 100):
                logger.error("Invalid humidity value")
                return api_response(success=False, error="Invalid humidity value"), 400
            try:
                sensor_data = SensorData(
                    timestamp=timestamp, temperature=temperature, humidity=humidity
                )
                db.session.add(sensor_data)
                db.session.commit()
            except Exception as e:
                return api_response(success=False, error=f"Database error: {str(e)}"), 500
            return api_response(success=True, data=data)
        except BleakError as e:
            log_error(f"BLE error: {e}")
            return api_response({"error": "Failed to interact with BLE device"}), 500
    except BleakError as e:
        log_error("get_device_data - BLE interaction", e)
        return api_response({"error": "Failed to interact with BLE device"}), 500
    except SQLAlchemyError as e:
        log_error("get_device_data - Database operation", e)
        return api_response({"error": "Database operation failed"}), 500
    except Exception as e:
        log_error("get_device_data - Unexpected error", e)
        return api_response({"error": "An unexpected error occurred"}), 500

@api.route('/start_background_task')
def start_background_task_route():
    mac_address = request.args.get('mac_address', '')
    result = background_tasks.start_background_discovery(mac_address)
    if result:
        return api_response({"message": "Background task started"}), 200
    else:
        return api_response({"error": "An error occurred while starting the background task"}), 400

@api.route('/add_device_record')
def add_device_record_route():
    try:
        temperature_value = request.args.get('temperature')
        humidity_value = request.args.get('humidity')
        services.add_new_device_record(temperature_value, humidity_value)
        return api_response({"message": "Record added successfully"}), 200
    except SQLAlchemyError as e:
        log_error(f"Database error: {e}")
        return api_response({"error": "Database operation failed"}), 500
    except Exception as e:
        log_error(f"Unexpected error: {e}")
    return api_response({"error": "An unexpected error occurred"}), 500



if __name__ == "__main__":
    thread = Thread(target=background_tasks.start_background_discovery_task, daemon=True)
    thread.start()

