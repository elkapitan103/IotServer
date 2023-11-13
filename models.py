from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from base import Base
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Boolean, DateTime
from datetime import datetime

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    connected = Column(Boolean, default=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    DeviceMetadata = Column(String, nullable=True)

    sensor_data = relationship('SensorData', back_populates='device') 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    device_detail = relationship('DeviceDetail', uselist=False, back_populates='device')

class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    value = Column(Float)
    metric = Column(String)
    unit = Column(String)
    device_id = Column(Integer, ForeignKey('devices.id'))

    device = relationship('Device', back_populates='sensor_data')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeviceDetail(Base):
    __tablename__ = 'device_details'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))

    status = Column(String)
    last_activity = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship('Device', back_populates='device_detail')
    
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(128))
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
