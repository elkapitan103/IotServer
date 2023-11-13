from models import SensorData
import logging
from discovery import initialize_discovery, start_discovery, get_discovered_devices

from services import get_sensor_data

from concurrent.futures import ThreadPoolExecutor
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask import Blueprint
from flask import jsonify, render_template, request, redirect, url_for, current_app

class DeviceForm(FlaskForm):
    device_name = StringField('Device Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

web = Blueprint('web', __name__)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor()

@web.route('/')
def index():
    try:
        initialize_discovery()
        start_discovery()
        devices = get_discovered_devices()
        # Use the devices list in your route logic
    except Exception as e:
        logger.error(f"Error initializing discovery components: {e}")
        return "An error occurred during initialization.", 500

ALLOWED_DEVICES = ["device1", "device2", "..."] 

@web.route('/select_device_web', methods=['POST'])
def select_device_web():
    selected_device_name = request.form.get('device_name')
    if not selected_device_name or selected_device_name.strip() == "":
        return jsonify(success=False, error="Device name is required"), 400
    if not selected_device_name or selected_device_name not in ALLOWED_DEVICES:
        return "Invalid or no device selected", 400
    current_app.config['SELECTED_DEVICE_NAME'] = selected_device_name
    return redirect(url_for('index'))
    
@web.route("/devices/<device_name>/data", methods=["GET"])
def get_data():
    selected_device_name = current_app.config.get('SELECTED_DEVICE_NAME')
    if not selected_device_name:
        return redirect(url_for('select_device')) 
    sensor_data_for_device = SensorData.query.filter_by(device_name=selected_device_name).all()
    data_list = [{"timestamp": data.timestamp, "temperature": data.temperature, "humidity": data.humidity} for data in sensor_data_for_device]
    return jsonify(success=True, data=data_list)

@web.route('/collect_data')
def collect_data():
    try:
        future = executor.submit(get_sensor_data)
        logger.info("Data collection process initiated.")
        return "Data collection started", 200
    except Exception as e:
        logger.error(f"Error collecting sensor data: {e}")
        return "Error collecting data", 500

@web.route('/latest_data')
def latest_data():
    try:
        latest_entry = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        logger.info(f"Successfully retrieved latest data with timestamp: {latest_entry.timestamp}.")
        return jsonify({
            'timestamp': latest_entry.timestamp,
            'temperature': latest_entry.temperature,
            'humidity': latest_entry.humidity
        })
    except Exception as e:
        logger.error(f"Error retrieving latest sensor data: {e}")
        return jsonify({'error': 'An error occurred while fetching the latest data.'})
    
@web.route('/display_data', methods=['GET'])
def display_data():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10  
        data = SensorData.query.order_by(SensorData.timestamp.desc()).paginate(page, per_page, False)
        logger.info(f"Fetched {len(data.items)} records for page {page}.")
        data_list = [{'timestamp': record.timestamp, 'temperature': record.temperature, 'humidity': record.humidity} for record in data]
        return render_template('display_data.html', data=data_list)
    except Exception as e:
        logger.error(f"Error displaying sensor data: {e}")
        return render_template('error.html', message='An error occurred while displaying data.')

@web.errorhandler(500)
def handle_500(error):
    return jsonify(success=False, error=str(error)), 500





