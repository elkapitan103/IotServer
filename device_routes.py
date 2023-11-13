from flask import jsonify, render_template, request, redirect
from flask import url_for, flash
from flask_jwt_extended import jwt_required
import logging

from models import DeviceMetadata
import services
from flask import Blueprint

device = Blueprint('device', __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@device.route('/add-device', methods=['POST'])
@jwt_required()
def add_device():
    data = request.json
    if not data or 'name' not in data or 'address' not in data or 'type' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    try:
        services.add_new_device(data['name'], data['address'], data['type'])
        return jsonify({"message": "Device added successfully!"}), 201
    except Exception as e:
        logger.error(f"Error adding device: {e}")
        return jsonify({"message": "Error adding device"}), 500

@device.route('/configure_device/<device_name>', methods=['GET', 'POST'])
@jwt_required()  # Ensure only logged-in users can access
def configure_device(device_name):
    try:
        if request.method == 'POST':
            flash('Device configured successfully!', 'success')
            return redirect(url_for('devices'))
        return render_template('configure_device.html', device_name=device_name)
    except Exception as e:
        logger.error(f"Error configuring device: {e}")
        return jsonify({"error": "Failed to configure device"}), 500

@device.route('/view_device/<device_name>', methods=['GET'])
def view_device(device_name):
    try:
        device = DeviceMetadata.query.filter_by(device_name=device_name).first()
        if not device:
            flash('Device not found!', 'danger')
            return redirect(url_for('devices'))
        return render_template('view_device.html', device=device)
    except Exception as e:  
        return jsonify(success=False, error=f"Database error: {str(e)}"), 500