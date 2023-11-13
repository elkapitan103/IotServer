from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_raw_jwt
import services

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username or password missing"}), 400
    response, status_code = services.handle_login(data)
    return jsonify(response), status_code

@auth.route('/refresh', methods=['POST'])
@jwt_refresh_token_required()
def refresh():
    response, status_code = services.handle_refresh_token()
    return jsonify(response), status_code

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_raw_jwt()['jti'] 
    response, status_code = services.handle_logout(jti)
    return jsonify(response), status_code