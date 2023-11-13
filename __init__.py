from flask import Flask, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from database import engine, init_db
from database import Session as db
from api_routes import api
from web_routes import web  
from base import Base
from config import config

app = Flask(__name__)
app.config.from_object('config.Config')

def get_remote_address():
    """Retrieve the IP address of the client making the request."""
    return request.remote_addr

limiter = Limiter(app, key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config.from_object(config.config)
    logging.basicConfig(level=app.config['LOG_LEVEL'])
    allowed_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    db.init_app(app)
    register_blueprints(app)  
    with app.app_context():
        Base.metadata.create_all(bind=engine)
    return app

def register_blueprints(app):
    app.register_blueprint(api) 
    app.register_blueprint(web)

if __name__ == "__main__":
    init_db()
