"""
Example Firebase Functions with Flask.
"""

from flask import Flask
from functions_wrapper import entrypoint

from firebase_functions import https_fn

app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello!"


@app.route("/world")
def world():
    return "Hello World!"


@https_fn.on_request()
def httpsflaskexample(request):
    return entrypoint(app, request)
