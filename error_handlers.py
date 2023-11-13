import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def handle_errors(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        logger.error(f"Bad request error: {error}")
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.warning(f"Unauthorized request: {error}")
        return jsonify({"error": "Unauthorized", "message": str(error)}), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"Forbidden request: {error}")
        return jsonify({"error": "Forbidden", "message": str(error)}), 403

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"Not found error: {error}")
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500
