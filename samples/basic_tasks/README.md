# IAM Policy

When a queued task calls the function `on_task_dispatched_example` from the sample, you will face permission errors.

First, the service account has to be granted the following permissions `cloudtasks.enqueuer` in order to enqueue tasks:

```bash
gcloud projects add-iam-policy-binding python-functions-testing \
  --member=serviceAccount:441947996129-compute@developer.gserviceaccount.com \
  --role=roles/cloudtasks.enqueuer
```

Then, the service account has to be granted the following permissions `cloudfunctions.invoker` in order to call the `on_task_dispatched_example` function:

```bash
gcloud functions add-iam-policy-binding on-task-dispatched-example \
  --region=us-central1 \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/cloudfunctions.invoker --gen2
```
