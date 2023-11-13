from utils import setup_logging, logger
from database import db_session_scope, Session as db
from config import TARGET_MAC_ADDRESS, DEVICE_NAME, SQLALCHEMY_TRACK_MODIFICATIONS, SQLALCHEMY_DATABASE_URI
from discovery import discover_devices, get_discovered_data
from __init__ import create_app
from web_routes import web
from api_routes import api 

from auth_routes import auth
from device_routes import device
from data_routes import data

from apscheduler.schedulers.background import BackgroundScheduler
import threading

MAX_RETRIES = 3

try:
    app = create_app()
except Exception as e:
    print(f'Error creating app: {e}')
    
app.register_blueprint(api)
app.register_blueprint(web)

app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(device, url_prefix='/device')
app.register_blueprint(data, url_prefix='/data')

def configure_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['DEVICE_NAME'] = DEVICE_NAME
    app.config['TARGET_MAC_ADDRESS'] = TARGET_MAC_ADDRESS
    setup_logging(app)
    db.init_app(app)

configure_app(app)

def run_discovery_on_startup():
    try:
        discovered_data = get_discovered_data()
        if validate_data(discovered_data):
            with db_session_scope() as session:
                session.add(discovered_data)
                logger.info("Data validation successful.")
        else:
            logger.error('Data validation failed')
    except Exception as e:
        logger.error(f"Error during data discovery or database operation: {e}")

def continuous_discovery():
    scheduler = BackgroundScheduler()
    scheduler.add_job(discover_and_store_data, 'interval', minutes=10)  
    scheduler.start()

def discover_and_store_data():
    with app.app_context():
        try:
            discovered_data = get_discovered_data()
            if validate_data(discovered_data):
                with db_session_scope() as session:  # Using the context manager
                    session.add(discovered_data)
            else:
                logger.error('Data validation failed')
        except Exception as e:
            logger.error(f"Error during data discovery or database operation: {e}")

def validate_data(data, retries=0):
    if "error" in data and retries < MAX_RETRIES:
        retries += 1
        logger.info("Discovery started...")
        discovered_data = get_discovered_data()
        logger.info(f"Discovered data: {discovered_data}")
        return validate_data(discovered_data, retries)
    elif retries >= MAX_RETRIES:
        logger.error("Maximum retries reached for data validation.")
        return False
    else:
        return True
try:
    discovered_data = get_discovered_data()
    if validate_data(discovered_data):
        with db_session_scope() as session:
            session.add(discovered_data)
            logger.info("Data validation successful.")
    else:
        logger.error('Data validation failed')
except Exception as e:
    logger.error(f"Error during data discovery or database operation: {e}")

run_discovery_on_startup()
continuous_discovery()

if __name__ == '__main__':
    discovery_thread = threading.Thread(target=discover_devices, args=(app,))
    discovery_thread.daemon = True
    discovery_thread.start()
    
    host = app.config.get('HOST', '127.0.0.1')  
    port = app.config.get('PORT', 5000)  
    debug = app.config.get('DEBUG', False)
    app.run(host=host, port=port, debug=debug)