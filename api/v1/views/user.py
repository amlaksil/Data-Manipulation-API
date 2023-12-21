#!/usr/bin/python3

"""
This module contains routes for user management in an API. It provides
functionality for creating, retrieving, and managing users. The module
uses Flask and SQLAlchemy for handling HTTP requests and interacting with
the database.

Dependencies
Flask: A micro web framework for Python.
SQLAlchemy: An SQL toolkit and Object-Relational Mapping (ORM) library for
Python.
bcrypt: A password hashing library for secure password storage.
jwt: A library for encoding and decoding JSON Web Tokens (JWT).
"""
import base64
import datetime
from functools import wraps
import os
import uuid

import jwt
import bcrypt
from flask import request, jsonify, make_response

from api.v1.views import app_views
from api.v1.views import db, app


class User(db.Model):
    """
    Represents a user in the database.

    Attributes:
        id: An integer representing the user's unique identifier.
        public_id: A string representing the user's public ID
        name: A string representing the user's name.
        password: A string representing the user's hashed password.
        admin: A boolean indicating whether the user is an admin or not.
    """
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


def token_required(f):
    """
    Decorator function to verify the access token provided in the request
    header.

    Args:
        f (function): The decorated function.

    Returns:
        function: The decorated function.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.

    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'access-token' in request.headers:
            token = request.headers['access-token']

        if not token:
            return jsonify({'error': 'Token is missing!'}), 400

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app_views.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    """
    Retrieves all users from the database.

    Args:
        current_user (User): The current authenticated user.

    Returns:
        flask.Response: JSON response with a list of user data.

    """
    try:
        if not current_user.admin:
            return jsonify({'message': 'Cannot perform that function!'}), 401
    except:
        return jsonify({'error': 'No user found!'}), 404

    users = User.query.all()

    output = []
    for user in users:
        user_data = {
                'public_id': user.public_id,
                'name': user.name,
                'password': base64.b64encode(user.password).decode('utf-8'),
                'admin': user.admin
        }

        output.append(user_data)

    return jsonify({'users': output}), 200


@app_views.route('/user/<public_id>', methods=['GET'])
def get_user(public_id):
    """
    Retrieves a specific user by their public ID.

    Args:
        public_id (str): The public ID of the user to retrieve.

    Returns:
        flask.Response: JSON response with the user data.

    """
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'error': 'No user found!'}), 404

    user_data = {
            'public_id': user.public_id,
            'name': user.name,
            'password': base64.b64encode(user.password).decode('utf-8'),
            'admin': user.admin
    }

    return jsonify({'message': user_data}), 200


@app_views.route('/user', methods=['POST'])
def create_user():
    """
    Creates a new user.

    Returns:
        flask.Response: JSON response with the created user id.
    """
    data = request.get_json()

    salt = bcrypt.gensalt()  # Generate a random salt
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)

    new_user = User(
            public_id=str(uuid.uuid4()),
            name=data['name'],
            password=hashed_password,
            admin=True
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created!'}), 200


@app_views.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(_, public_id):
    """
    Deletes a specific user by their public ID.

    Args:
        public_id (str): The public ID of the user to delete.

    Returns:
        flask.Response: JSON response indicating the success of the deletion.
    """
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'error': 'No user found!'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'The user has been deleted!'}), 200


@app_views.route('/login')
def login():
    """
    Authenticates a user and generates an access token.

    Returns:
        flask.Response: JSON response with the access token.

    Raises:
        flask.abort: If the authentication credentials are missing
        or incorrect.
    """
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return jsonify({
                'error': 'Missing credentials. Please provide a username and\
                password.'}), 400
    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return jsonify({'error': 'No user found!'}), 404

    entered_password = auth.password.encode('utf-8')
    if bcrypt.checkpw(entered_password, user.password):
        token = jwt.encode({
                'public_id': user.public_id,
                'exp': datetime.datetime.utcnow() +
                datetime.timedelta(minutes=30)},
                app.config['SECRET_KEY']
        )
        return jsonify({'token': token.decode('UTF-8')}), 200

    return jsonify({'error': 'Incorrect password.'}), 401
