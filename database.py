from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
import logging
from config import SQLALCHEMY_DATABASE_URI
from models import DeviceDetail
from base import Base

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

def init_db():
    Base.metadata.create_all(bind=engine)

def get_all_device_details():
    with db_session_scope() as session:
        return session.query(DeviceDetail).all()

def validate_device_detail(device_name, status, last_activity):
    # This is a generic validation. Adjust as per your requirements.
    if not device_name or not status or not last_activity:
        return False
    return True


@contextmanager
def db_session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def add_device_detail(device_name, status, last_activity):
    if not validate_device_detail(device_name, status, last_activity):
        return {"status": "error", "message": "Invalid device details"}
    try:
        with db_session_scope() as session:
            device = session.query(DeviceDetail).filter_by(device_name=device_name).first()
            if device:
                device.status = status
                device.last_activity = last_activity
                logger.info(f"Updated device detail for {device_name}")
                return {"status": "success", "message": "Device detail updated successfully"}
            else:
                device_detail = DeviceDetail(device_name=device_name, status=status, last_activity=last_activity)
                session.add(device_detail)
                logger.info(f"Added new device detail for {device_name}")
                return {"status": "success", "message": "Device detail added successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Error in add_device_detail: {e}")
        return {"status": "error", "message": f"Database error: {e}"}

def delete_device_detail(device_name):
    try:
        with db_session_scope() as session:
            device = session.query(DeviceDetail).filter_by(device_name=device_name).first()
            if device:
                session.delete(device)
                return {"status": "success", "message": "Device detail deleted successfully"}
            else:
                return {"status": "error", "message": "Device detail not found"}
    except SQLAlchemyError as e:
        logger.error(f"Error in delete_device_detail: {e}")
        return {"status": "error", "message": f"Database error: {e}"}

def modify_device_detail(device_name, status=None, last_activity=None):
    try:
        with db_session_scope() as session:
            device = session.query(DeviceDetail).filter_by(device_name=device_name).first()
            if not device:
                device = DeviceDetail(device_name=device_name)
                session.add(device)
            if status is not None:
                device.status = status
            if last_activity is not None:
                device.last_activity = last_activity
            return {"status": "success", "message": "Device detail modified successfully"}
    except Exception as e:
        logger.error(f"Error in modify_device_detail: {e}")
        raise DatabaseError(f"Error while modifying device detail: {e}")

def get_device_detail_by_name(device_name):
    try:
        with db_session_scope() as session:
            device = session.query(DeviceDetail).filter_by(device_name=device_name).first()
            return device
    except Exception as e:
        logger.error(f"Error in get_device_detail_by_name: {e}")
        raise DatabaseError(f"Error while fetching device detail: {e}")

def initialize_database():
    Base.metadata.create_all(engine)




