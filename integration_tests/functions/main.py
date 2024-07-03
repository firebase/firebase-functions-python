# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app

initialize_app()

@https_fn.on_call()
def hello(_: https_fn.CallableRequest) -> str:
    return 'Hello from Firebase!'