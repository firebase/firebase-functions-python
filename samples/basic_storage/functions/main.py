"""
Example Firebase Functions for Storage triggers.
"""

from firebase_admin import initialize_app

from firebase_functions import storage_fn
from firebase_functions.storage_fn import CloudEvent, StorageObjectData

initialize_app()


@storage_fn.on_object_finalized()
def onobjectfinalizedexample(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when a new object is created in the bucket.
    """
    print(event)


@storage_fn.on_object_archived()
def onobjectarchivedexample(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object is archived in the bucket.
    """
    print(event)


@storage_fn.on_object_deleted()
def onobjectdeletedexample(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object is deleted in the bucket.
    """
    print(event)


@storage_fn.on_object_metadata_updated()
def onobjectmetadataupdatedexample(event: CloudEvent[StorageObjectData]):
    """
    This function will be triggered when an object's metadata is updated in the bucket.
    """
    print(event)
