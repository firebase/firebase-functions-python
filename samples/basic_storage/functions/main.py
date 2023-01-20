"""Basic Storage triggers example."""

from firebase_functions import storage
from firebase_functions.storage import StorageObjectData, CloudEvent
from firebase_admin import initialize_app

initialize_app()
BUCKET = "python-functions-testing.appspot.com"


@storage.on_object_finalized(bucket=BUCKET)
def on_object_finalized_example(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when a new object is created in the bucket.
    """
    print(event)


@storage.on_object_archived(bucket=BUCKET)
def on_object_archived_example(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object is archived in the bucket.
    """
    print(event)


@storage.on_object_deleted(bucket=BUCKET)
def on_object_deleted_example(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object is deleted in the bucket.
    """
    print(event)


@storage.on_object_metadata_updated(bucket=BUCKET)
def on_object_metadata_updated_example(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object's metadata is updated in the bucket.
    """
    print(event)
