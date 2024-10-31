from firebase_admin import firestore
from firebase_functions.firestore_fn import (on_document_created, Event,
                                             DocumentSnapshot,
                                             on_document_deleted,
                                             on_document_updated,
                                             on_document_written)
from region import REGION


@on_document_created(document='tests/{documentId}',
                     region=REGION,
                     timeout_sec=540)
def firestoreOnDocumentCreatedTests(event: Event[DocumentSnapshot]):
    document_id = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentCreatedTests').document(
        document_id).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@on_document_deleted(document='tests/{documentId}',
                     region=REGION,
                     timeout_sec=540)
def firestoreOnDocumentDeletedTests(event: Event[DocumentSnapshot]):
    document_id = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentDeletedTests').document(
        document_id).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@on_document_updated(document='tests/{documentId}',
                     region=REGION,
                     timeout_sec=540)
def firestoreOnDocumentUpdatedTests(event: Event[DocumentSnapshot]):
    document_id = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentUpdatedTests').document(
        document_id).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@on_document_written(document='tests/{documentId}',
                     region=REGION,
                     timeout_sec=540)
def firestoreOnDocumentWrittenTests(event: Event[DocumentSnapshot]):
    document_id = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentWrittenTests').document(
        document_id).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })
