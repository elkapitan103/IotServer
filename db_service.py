from flask import request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime
import logging

from database import Session as db
from models import DeviceMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_to_db(record):
    try:
        with db() as session:
            session.add(record)
            session.commit()
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def fetch_request_data():
    device_name = request.form.get('device_name')
    status = request.form.get('status')
    last_activity = request.form.get('last_activity')
    return device_name, status, last_activity

def validate_status(status):
    valid_statuses = ["active", "inactive", "pending", "error"]  
    if not status or status not in valid_statuses:
        logger.error(f"Invalid status value: {status}")
        return jsonify({"error": "Invalid status value"}), 400
    return None

def parse_last_activity(last_activity):
    try:
        parsed_activity = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
        return parsed_activity
    except ValueError:
        logger.error(f"Invalid last_activity format: {last_activity}")
        return jsonify({"error": "Invalid last_activity format"}), 400
    
def handle_db_error(e):
    current_app.logger.error(f"Database error: {e}")
    db.session.rollback()
    return jsonify({"error": "Failed to update database"}), 500

def get_device_details_from_db():
    return DeviceMetadata.query.all()

def fetch_all_devices():
    try:
        with db() as session:
            devices = session.query(DeviceMetadata).all()
        return devices
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return None