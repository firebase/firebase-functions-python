import json

from firebase_admin import firestore
from firebase_functions.eventarc_fn import (on_custom_event_published,
                                            CloudEvent)


@on_custom_event_published(event_type="achieved-leaderboard")
def eventarcOnCustomEventPublishedTests(event: CloudEvent):
    test_id = event.data["testId"]

    firestore.client().collection(
        "eventarcOnCustomEventPublishedTests").document(test_id).set({
            "id": event.id,
            "type": event.type,
            "time": event.time,
            "source": event.source,
            "data": json.dumps(event.data),
        })
