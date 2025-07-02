# app.py

from flask import Flask
from get_credentials import get_and_write_creds
from update import update
from query_app import search
import os

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET_KEY']

# OAuth flow
app.add_url_rule('/authorize', view_func=get_and_write_creds)
app.add_url_rule('/oauth2callback', view_func=update)

# Query endpoint
app.add_url_rule('/search', view_func=search, methods=["POST"])
