from firebase_admin import firestore
from firebase_functions.remote_config_fn import (on_config_updated, CloudEvent,
                                                 ConfigUpdateData)

from region import REGION


@on_config_updated(region=REGION)
def remoteConfigOnConfigUpdatedTests(
        event: CloudEvent[ConfigUpdateData]) -> None:
    test_id = event.data.description

    firestore.client().collection("remoteConfigOnConfigUpdatedTests").document(
        test_id).set({
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
        })
