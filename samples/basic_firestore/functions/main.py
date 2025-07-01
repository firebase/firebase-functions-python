"""
Example Firebase Functions for Firestore written in Python
"""

from firebase_functions import firestore_fn, options
from firebase_admin import initialize_app

initialize_app()

options.set_global_options(region=options.SupportedRegion.EUROPE_WEST1)


@firestore_fn.on_document_written(document="hello/{world}")
def onfirestoredocumentwritten(event: firestore_fn.Event[firestore_fn.Change]) -> None:
    print("Hello from Firestore document write event:", event)


@firestore_fn.on_document_created(document="hello/world")
def onfirestoredocumentcreated(event: firestore_fn.Event) -> None:
    print("Hello from Firestore document create event:", event)


@firestore_fn.on_document_deleted(document="hello/world")
def onfirestoredocumentdeleted(event: firestore_fn.Event) -> None:
    print("Hello from Firestore document delete event:", event)


@firestore_fn.on_document_updated(document="hello/world")
def onfirestoredocumentupdated(event: firestore_fn.Event[firestore_fn.Change]) -> None:
    print("Hello from Firestore document updated event:", event)
