# Cloud Functions for Firebase Python SDK (Public Preview)

The [`firebase-functions`](https://pypi.org/project/firebase-functions/) package provides an SDK for defining Cloud Functions for Firebase in Python.

Cloud Functions provides hosted, private, and scalable environment where you can run server code. The Firebase SDK for Cloud Functions integrates the Firebase platform by letting you write code that responds to events and invokes functionality exposed by other Firebase features.

## Learn more

Learn more about the Firebase SDK for Cloud Functions in the [Firebase documentation](https://firebase.google.com/docs/functions/) or [check out our samples](https://github.com/firebase/functions-samples).

Here are some resources to get help:

- Start with the quickstart: https://firebase.google.com/docs/functions/get-started
- Go through the guide: https://firebase.google.com/docs/functions/
- Read the full API reference: https://firebase.google.com/docs/reference/functions/2nd-gen/python
- Browse some examples: https://github.com/firebase/functions-samples

If the official documentation doesn't help, try asking through our official support channels: https://firebase.google.com/support/

## Usage

```python
# functions/main.py
from firebase_functions import db_fn
from notify_users import api

@db_fn.on_value_created(reference="/posts/{post_id}")
def new_post(event):
    print(f"Received new post with ID: {event.params.get('post_id')}")
    return notifyUsers(event.data)
```

## Contributing

To contribute a change, [check out the contributing guide](.github/CONTRIBUTING.md).

## License

© Google, 2023. Licensed under [Apache License](LICENSE).