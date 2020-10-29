# Created by: Mathieu Gilli
# Goal: Gain insights into spotify usage

# Define imports/dependencies
from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import uuid
import os

# Secret Key Generator
## import secrets
## generated_key = secrets.token_urlsafe(20)
## print(generated_key)

# Initiate flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

# Initiate DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', "sqlite:///myDB.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Uses SQLAlchemy as a session backend
# This was implemented https://github.com/mnbf9rca/flask-session/commit/9ad4b23e946beba1fdbd23dc406058a77dac6676 (flask_session/sessions.py line 515 becomes: if saved_session and (not saved_session.expiry or saved_session.expiry <= datetime.utcnow()):)
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SESSION_SQLALCHEMY"] = db
Session(app)

# Configure Celery app
## run this to start celery : celery -A spotapp.celery worker --pool=gevent --loglevel=INFO
## run this to purge all pending tasks: celery -A spotapp.celery purge
app.config["CELERY_BROKER_URL"] = "amqp://local:devCELERY8@localhost:5672/myvhost"
app.config["CELERY_BACKEND"] = "rpc://"

# Initiate celery app
from spotapp.flask_celery import make_celery
celery = make_celery(app)

# Import flask app routes
import spotapp.hub
import spotapp.genrewordmap
import spotapp.trackcluster
import spotapp.trackclusterresult
import spotapp.createplaylist
