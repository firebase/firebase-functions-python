"""Basic Pub/Sub example."""

from firebase_functions import pubsub
from firebase_admin import initialize_app

initialize_app()


@pubsub.on_message_published(topic="hello")
def on_message_published_example(
        event: pubsub.CloudEvent[pubsub.MessagePublishedData]) -> None:
    """
    This function will be triggered when a message is published to the topic.
    """
    print("Hello from pubsub event:", event)
