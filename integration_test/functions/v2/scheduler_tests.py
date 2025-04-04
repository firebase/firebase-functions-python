from firebase_admin import firestore
from firebase_functions import logger
from firebase_functions.scheduler_fn import (on_schedule, ScheduledEvent)

from region import REGION


@on_schedule(schedule="every 10 hours", region=REGION)
def schedule(event: ScheduledEvent):
    test_id = event.job_name
    if test_id is None:
        logger.error("TestId not found for scheduled function execution")
        return

    firestore.client().collection("schedulerOnScheduleV2Tests").document(
        test_id).set({"success": True})
