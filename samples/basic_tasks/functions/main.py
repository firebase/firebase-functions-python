"""Firebase Cloud Functions for Tasks."""
from firebase_admin import initialize_app
from firebase_functions import tasks_fn
from firebase_functions.options import SupportedRegion, RetryConfig, RateLimits

app = initialize_app()


# Once this function is deployed, a Task Queue will be created with the name
# `ontaskdispatchedexample`.
@tasks_fn.on_task_dispatched(
    retry_config=RetryConfig(max_attempts=5),
    rate_limits=RateLimits(max_concurrent_dispatches=10),
    region=SupportedRegion.US_CENTRAL1,
)
def ontaskdispatchedexample(req: tasks_fn.CallableRequest):
    """
    The endpoint which will be executed by the enqueued task.
    """
    print(req.data)
