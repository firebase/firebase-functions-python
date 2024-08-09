from firebase_admin import firestore
from firebase_functions.identity_fn import (before_user_created,
                                            BeforeCreateResponse,
                                            before_user_signed_in,
                                            BeforeSignInResponse,
                                            AuthBlockingEvent)


@before_user_created()
def identityBeforeUserCreatedTests(
        event: AuthBlockingEvent) -> BeforeCreateResponse:
    uid = event.data.uid

    firestore.client().collection("identityBeforeUserCreatedTests").document(
        uid).set({
            "eventId": event.event_id,
            "timestamp": event.timestamp,
        })

    return BeforeCreateResponse(**event.data.__dict__)


@before_user_signed_in()
def identityBeforeUserSignedInTests(
        event: AuthBlockingEvent) -> BeforeSignInResponse:
    uid = event.data.uid

    firestore.client().collection("identityBeforeUserSignedInTests").document(
        uid).set({
            "eventId": event.event_id,
            "timestamp": event.timestamp,
        })
