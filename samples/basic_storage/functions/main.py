from firebase_functions import storage
from firebase_admin import initialize_app
from firebase_functions.storage import StorageObjectData, CloudEvent

initialize_app()


@storage.on_object_finalized(bucket="python-functions-testing.appspot.com")
def on_object_finalized_example(event: CloudEvent[StorageObjectData]):
    print(event)
