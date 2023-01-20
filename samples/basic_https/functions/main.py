"""Basic HTTPS example."""

from firebase_functions import https, options, params
from firebase_admin import initialize_app

initialize_app()

options.set_global_options(
    region=options.SupportedRegion.EUROPE_WEST1,
    memory=options.MemoryOption.MB_128,
    min_instances=params.IntParam("MIN", default=3),
)


@https.on_request()
def on_request_https_example(req: https.Request) -> https.Response:
    """
    This function will be triggered when a request is made to the endpoint.
    """
    print(req)
    return https.Response("Hello world!")


@https.on_call()
def on_call_https_example(req: https.CallableRequest):
    """
    This function will be triggered when a request is made to the endpoint
    using Firebase Function SDKs.
    """
    print(req)
    return "Hello world!"
