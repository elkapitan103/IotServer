import logging
from logging.handlers import RotatingFileHandler
from celery import Celery
from flask import jsonify

from database import Session as db
from data_helpers import extract_data, process_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_celery(app):
    try:
        celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
        celery.conf.update(app.config)
        return celery
    except Exception as e:
        logger.error(f"Error initializing Celery: {e}")
        return None

def setup_logging(app):
    try:
        if app.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
            handler.setLevel(logging.INFO)
            app.logger.addHandler(handler)
    except Exception as e:
        logger.error(f"Error setting up logging: {e}")

def init_app(app):
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

def is_data_valid(data):
    try:
        extracted_data = extract_data(data)
        processed_data = process_data(extracted_data)
        required_fields = ["timestamp", "temperature", "humidity"]
        return all(field in processed_data for field in required_fields)
    except Exception as e:
        logger.error(f"Error validating data: {e}")
        return False

def filter_data(data, start_time, end_time):
    return [record for record in data if "timestamp" in record and start_time <= record["timestamp"] <= end_time]

def error_response(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response



