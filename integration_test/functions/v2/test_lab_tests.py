from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.test_lab_fn import (on_test_matrix_completed,
                                            CloudEvent, TestMatrixCompletedData)

from region import REGION


@on_test_matrix_completed(region=REGION)
def testLabOnTestMatrixCompletedTests(
        event: CloudEvent[TestMatrixCompletedData]) -> None:
    test_id = event.data.client_info.details["testId"]

    firestore.client().collection("testLabOnTestMatrixCompletedTests").document(
        test_id).set({
            "testId": test_id,
            "type": event.type,
            "id": event.id,
            "time": event.time,
            "state": event.data.state
        })
