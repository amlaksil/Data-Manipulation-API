#!/usr/bin/python3

from os import getenv

from flask import Flask, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from api.v1.views import app_views, app, db

app.register_blueprint(app_views)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
CORS(app, resources={r"/api/v1/*": {"origins": "*"}})


@app.errorhandler(401)
def handle_unauthorized_error(error) -> str:
    """
    Handles the 401 Unauthorized error.

    Args:
            error (Exception): The exception object representing the error.

    Returns:
            str: JSON-encoded string containing the error message.
    """
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(404)
def not_found(error):
    """404 Error

    responses:
        404 Not Found: requested resource (e.g., a specific URL or endpoint)
    does not exist on the server.
    """
    return make_response(jsonify({'error': "Not found"}), 404)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the necessary tables
    app.run(debug=False)
