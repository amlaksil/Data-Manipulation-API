#!/usr/bin/python3

"""
This module defines a Flask Blueprint for handling API views
related to version 1 ("/api/v1").
"""
from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.url_map.strict_slashes = False

db = SQLAlchemy(app)
app_views = Blueprint("app_views", __name__, url_prefix="/api/v1")

from api.v1.views import data, user
