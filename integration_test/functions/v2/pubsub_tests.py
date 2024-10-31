import json

from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.pubsub_fn import (on_message_published, CloudEvent,
                                          MessagePublishedData)

from region import REGION


@on_message_published(topic="custom_message_tests", region=REGION)
def pubsubOnMessagePublishedTests(
        event: CloudEvent[MessagePublishedData[dict]]) -> None:
    json_data = event.data.message.json
    if json_data is None:
        logger.error("Message is not JSON")
        return

    test_id = json_data["testId"]

    firestore.client().collection("pubsubOnMessagePublishedTests").document(
        test_id).set({
            "id": event.id,
            "source": event.source,
            "subject": event.subject,
            "time": event.time,
            "type": event.type,
            "message": json.dumps(event.data.message),
        })
