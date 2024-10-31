from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.storage_fn import (on_object_deleted,
                                           on_object_finalized,
                                           on_object_metadata_updated,
                                           CloudEvent, StorageObjectData)

from region import REGION


@on_object_deleted(region=REGION)
def storageOnDeleteTests(event: CloudEvent[StorageObjectData]) -> None:
    test_id = event.data.name.split(".")[0]
    if test_id is None:
        logger.error("TestId not found for storage onObjectDeleted")
        return

    firestore.client().collection("storageOnObjectDeletedTests").document(
        test_id).set({
            "id": event.id,
            "time": event.time,
            "type": event.type,
            "source": event.source,
        })


@on_object_finalized(region=REGION)
def storageOnFinalizeTests(event: CloudEvent[StorageObjectData]) -> None:
    test_id = event.data.name.split(".")[0]
    if test_id is None:
        logger.error("TestId not found for storage onObjectFinalized")
        return

    firestore.client().collection("storageOnObjectFinalizedTests").document(
        test_id).set({
            "id": event.id,
            "time": event.time,
            "type": event.type,
            "source": event.source,
        })


@on_object_metadata_updated(region=REGION)
def storageOnMetadataUpdateTests(event: CloudEvent[StorageObjectData]) -> None:
    test_id = event.data.name.split(".")[0]
    if test_id is None:
        logger.error("TestId not found for storage onObjectMetadataUpdated")
        return

    firestore.client().collection(
        "storageOnObjectMetadataUpdatedTests").document(test_id).set({
            "id": event.id,
            "time": event.time,
            "type": event.type,
            "source": event.source,
        })
