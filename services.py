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





