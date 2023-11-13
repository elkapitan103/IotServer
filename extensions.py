
from flask_bcrypt import Bcrypt
from redis import Redis

bcrypt = Bcrypt()
redis_client = None

def initialize_extensions(app):
    bcrypt.init_app(app)
    global redis_client
    redis_client = Redis(app.config['REDIS_HOST'], app.config['REDIS_PORT'])
