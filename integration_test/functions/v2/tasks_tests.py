from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.tasks_fn import (on_task_dispatched, CallableRequest)

from region import REGION


@on_task_dispatched(region=REGION)
def tasksOnTaskDispatchedTests(request: CallableRequest):
    test_id = request.data["testId"]

    firestore.client().collection("tasksOnTaskDispatchedTests").document(
        test_id).set({"testId": test_id})
