from flask import Blueprint, jsonify, request
from datetime import datetime

from data_ops import store_data_background
from database import Session as db
from utils import is_data_valid
import services

from __init__ import limiter 

data = Blueprint('data', __name__)

@data.route("/iotdata", methods=["POST"])
@limiter.limit("5 per minute") 
def receive_iot_data():
    data = request.get_json()
    if not data or 'temperature' not in data:
        return jsonify({"error": "Invalid or incomplete data"}), 400
    processed_data = is_data_valid(data)
    if processed_data:  
        store_data_background.delay(processed_data)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Invalid data format"}), 400

@data.route("/iotdata", methods=["GET"])
def get_iot_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    with db() as session:
        sensor_data = services.fetch_all_sensor_data().paginate(page, per_page, error_out=False)
    data_list = [
        {
            "timestamp": record.timestamp.isoformat(),
            "temperature": record.temperature,
            "humidity": record.humidity,
        }
        for record in sensor_data.items
    ]
    return jsonify(data_list)

@data.route("/filter_data", methods=["GET"])
def get_filtered_data():
    start_time_str = request.args.get("start")
    end_time_str = request.args.get("end")
    if not start_time_str or not end_time_str:
        return jsonify({"error": "Both start and end times are required"}), 400
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        filtered_data = services.fetch_filtered_sensor_data(start_time, end_time)
        return jsonify(
            [
                {
                    "timestamp": record.timestamp.isoformat(),
                    "temperature": record.temperature,
                    "humidity": record.humidity,
                }
                for record in filtered_data
            ]
        )
    except ValueError:
        return jsonify({"error": "Invalid start or end date format"}), 400

    
