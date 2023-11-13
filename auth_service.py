from flask_jwt_extended import create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt
from models import User
from utils import error_response

bcrypt = Bcrypt()

def handle_login(data):
    user = User.query.filter_by(username=data.get('username')).first()
    if user and bcrypt.check_password_hash(user.password, data.get('password')):
        access_token = create_access_token(identity=data.get('username'))
        return {"access_token": access_token}, 200
    else:
        return error_response("Invalid credentials", 401)

def handle_refresh_token():
    #Handle the refresh token operation.
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return {"access_token": new_token}, 200

def handle_logout(jti, redis_client):
    redis_client.set(jti, 'true', ex=86400)
    return {"message": "Successfully logged out."}, 200