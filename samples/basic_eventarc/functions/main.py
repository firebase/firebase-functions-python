"""Firebase Cloud Functions for Eventarc triggers example."""
from firebase_functions import eventarc_fn


@eventarc_fn.on_custom_event_published(
    event_type="firebase.extensions.storage-resize-images.v1.complete",)
def onimageresize(event: eventarc_fn.CloudEvent) -> None:
    """
    Handle image resize events from the Firebase Storage Resize Images extension.
    https://extensions.dev/extensions/firebase/storage-resize-images
    """
    print("Received image resize completed event", event)
