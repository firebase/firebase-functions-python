"""Firebase Scheduled Cloud Functions example."""

from firebase_functions import scheduler_fn


@scheduler_fn.on_schedule(
    schedule="* * * * *",
    timezone=scheduler_fn.Timezone("America/Los_Angeles"),
)
def example(event: scheduler_fn.ScheduledEvent) -> None:
    print(event.job_name)
    print(event.schedule_time)
