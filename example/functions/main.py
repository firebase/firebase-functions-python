"""
Example Firebase Functions written in Python
"""
from firebase_functions import db, options, https, params, pubsub
from firebase_admin import initialize_app

initialize_app()

options.set_global_options(
    region=options.SupportedRegion.EUROPE_WEST1,
    memory=options.MemoryOption.MB_128,
    min_instances=params.IntParam("MIN", default=3),
)


@db.on_value_written(
    reference="hello",
    region=options.SupportedRegion.EUROPE_WEST1,
)
def on_write_example(event: db.DatabaseEvent[db.Change[object]]) -> None:
    print("Hello from db write event:", event)


@db.on_value_created(reference="hello/{any_thing_here}/bar")
def on_created_example(event: db.DatabaseEvent[object]) -> None:
    print("Hello from db create event:", event)


@db.on_value_deleted(reference="hello/{any_thing_here}/bar")
def on_deleted_example(event: db.DatabaseEvent[object]) -> None:
    print("Hello from db delete event:", event)


@db.on_value_updated(reference="hello")
def on_updated_example(event: db.DatabaseEvent[db.Change[object]]) -> None:
    print("Hello from db updated event:", event)


@https.on_request()
def on_request_example(req: https.Request) -> https.Response:
    print("on request function data:", req.data)
    return https.Response("Hello from https on request function example")


@https.on_call()
def on_call_example(req: https.CallableRequest):
    print("on call function data:", req)
    if req.data == "error_test":
        raise https.HttpsError(
            https.FunctionsErrorCode.INVALID_ARGUMENT,
            "This is a test",
            "This is some details of the test",
        )
    return "Hello from https on call function example"


@pubsub.on_message_published(
    topic="hello",)
def on_message_published_example(
        event: pubsub.CloudEvent[pubsub.MessagePublishedData]) -> None:
    print("Hello from pubsub event:", event)
