"""Firebase Cloud Functions for Tasks."""

import datetime
import json

from firebase_admin import initialize_app
from google.cloud import tasks_v2
from firebase_functions import tasks_fn, https_fn
from firebase_functions.options import SupportedRegion, RetryConfig, RateLimits

app = initialize_app()


# Once this function is deployed, a Task Queue will be created with the name
# `on_task_dispatched_example`. You can then enqueue tasks to this queue by
# calling the `enqueue_task` function.
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


# To enqueue a task, you can use the following function.
# e.g.
# curl -X POST -H "Content-Type: application/json" \
#   -d '{"data": "Hello World!"}' \
#   https://enqueue-task-<projectHash>-<region>.a.run.app\
@https_fn.on_request()
def enqueuetask(req: https_fn.Request) -> https_fn.Response:
    """
    Enqueues a task to the queue `on_task_dispatched_function`.
    """
    client = tasks_v2.CloudTasksClient()

    # The URL of the `on_task_dispatched_function` function.
    # Must be set to the URL of the deployed function.

    url = req.json.get("url") if req.json else None

    body = {"data": req.json}

    task: tasks_v2.Task = tasks_v2.Task(
        **{
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {"Content-type": "application/json"},
                "body": json.dumps(body).encode(),
            },
            "schedule_time": datetime.datetime.utcnow() + datetime.timedelta(minutes=1),
        }
    )

    parent = client.queue_path(
        app.project_id,
        SupportedRegion.US_CENTRAL1,
        "ontaskdispatchedexample2",
    )

    client.create_task(request={"parent": parent, "task": task})
    return https_fn.Response("Task enqueued.")
