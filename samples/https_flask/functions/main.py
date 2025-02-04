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

@https_fn.on_call()
def callableexample(request: https_fn.CallableRequest):
    return request.data

@https_fn.on_call()
def streamingcallable(request: https_fn.CallableRequest):
    yield "Hello,"
    yield "world!"
    return request.data
