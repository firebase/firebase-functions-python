"""
Example Firebase Functions written in Python
"""

from firebase_functions import https_fn, options, params, pubsub_fn
from firebase_admin import initialize_app

initialize_app()

options.set_global_options(
    region=options.SupportedRegion.EUROPE_WEST1,
    memory=options.MemoryOption.MB_128,
    min_instances=params.IntParam("MIN", default=3),
)


@https_fn.on_request()
def onrequestexample(req: https_fn.Request) -> https_fn.Response:
    print("on request function data:", req.data)
    return https_fn.Response("Hello from https on request function example")


@https_fn.on_call()
def oncallexample(req: https_fn.CallableRequest):
    print("on call function data:", req)
    if req.data == "error_test":
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            "This is a test",
            "This is some details of the test",
        )
    return "Hello from https on call function example"


@pubsub_fn.on_message_published(
    topic="hello",
)
def onmessagepublishedexample(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:
    print("Hello from pubsub event:", event)
