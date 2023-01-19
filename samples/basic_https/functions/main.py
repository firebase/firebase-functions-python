from firebase_functions import https
from firebase_admin import initialize_app

initialize_app()


@https.on_request()
def on_request_https_example(req: https.Request) -> https.Response:
    return https.Response("Hello world!")


@https.on_call()
def on_call_https_example(req: https.CallableRequest):
    return "Hello world!"
