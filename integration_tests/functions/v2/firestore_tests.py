from firebase_admin import firestore
from firebase_functions import firestore_fn, logger
from region import REGION


@firestore_fn.on_document_created(document='tests/{documentId}',
                                  region=REGION,
                                  timeout_sec=540)
def firestoreOnDocumentCreatedTests(
        event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    documentId = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentCreatedTests').document(
        documentId).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@firestore_fn.on_document_deleted(document='tests/{documentId}',
                                  region=REGION,
                                  timeout_sec=540)
def firestoreOnDocumentDeletedTests(
        event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    documentId = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentDeletedTests').document(
        documentId).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@firestore_fn.on_document_updated(document='tests/{documentId}',
                                  region=REGION,
                                  timeout_sec=540)
def firestoreOnDocumentUpdatedTests(
        event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    documentId = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentUpdatedTests').document(
        documentId).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })


@firestore_fn.on_document_written(document='tests/{documentId}',
                                  region=REGION,
                                  timeout_sec=540)
def firestoreOnDocumentWrittenTests(
        event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    documentId = event.params['documentId']

    firestore.client().collection('firestoreOnDocumentWrittenTests').document(
        documentId).set({
            'time': event.time,
            'id': event.id,
            'type': event.type,
            'source': event.source,
        })
