import json

from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.db_fn import (on_value_created, Event, on_value_deleted,
                                      on_value_updated, on_value_written,
                                      Change)

from region import REGION


@on_value_created(reference="databaseCreatedTests/{testId}/start",
                  region=REGION)
def databaseCreatedTests(event: Event[object]):
    test_id = event.params['testId']

    firestore.client().collection("databaseCreatedTests").document(test_id).set(
        {
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
            "url": event.reference,
        })


@on_value_deleted(reference="databaseDeletedTests/{testId}/start",
                  region=REGION)
def databaseDeletedTests(event: Event[object]):
    test_id = event.params['testId']

    firestore.client().collection("databaseDeletedTests").document(test_id).set(
        {
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
            "url": event.reference,
        })


@on_value_updated(reference="databaseUpdatedTests/{testId}/start",
                  region=REGION)
def databaseUpdatedTests(event: Event[Change[object]]):
    test_id = event.params['testId']
    data = event.data.after

    firestore.client().collection("databaseUpdatedTests").document(test_id).set(
        {
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
            "url": event.reference,
            "data": json.dumps(data if data is not None else {})
        })


@on_value_written(reference="databaseWrittenTests/{testId}/start",
                  region=REGION)
def databaseWrittenTests(event: Event[Change[object]]):
    test_id = event.params['testId']
    if event.data.after is None:
        logger.info(
            f"Event for {test_id} is None; presuming data cleanup, so skipping."
        )
        return

    firestore.client().collection("databaseWrittenTests").document(test_id).set(
        {
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
            "url": event.reference,
        })
