import os
import logging
from zeroconf import Zeroconf, ServiceListener
from flask import Flask

# Base Configuration
class Config:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HOST = "0.0.0.0"
    PORT = 8080
    DEVICE_NAME = None
    TARGET_MAC_ADDRESS = None
    CHARACTERISTIC_UUID = None
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', ["http://localhost:3000"])
    LOGGING_LEVEL = logging.INFO

# Development Configuration
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_SQLALCHEMY_DATABASE_URI', "sqlite:///sensor_data_dev.db")
    LOGGING_LEVEL = logging.DEBUG

# Production Configuration
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_SQLALCHEMY_DATABASE_URI', "sqlite:///sensor_data_prod.db")
    LOGGING_LEVEL = logging.INFO
    
# Testing Configuration
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_SQLALCHEMY_DATABASE_URI', "sqlite:///sensor_data_test.db")

# Dynamically set the configuration based on the ENVIRONMENT variable
environment = os.environ.get('ENVIRONMENT', 'development')
if environment == 'development':
    config = DevelopmentConfig
elif environment == 'production':
    config = ProductionConfig
elif environment == 'testing':
    config = TestingConfig
else:
    raise ValueError(f"Invalid environment name: {environment}")

    config = Config

SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')  # It's essential to change the default in production

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

zeroconf = Zeroconf()
listener = ServiceListener()

app = Flask(__name__)
app.config.from_object('config.Config')
