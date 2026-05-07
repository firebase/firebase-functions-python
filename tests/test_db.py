"""
Tests for the db module.
"""

import datetime as dt
import unittest
from unittest import mock

from cloudevents.http import CloudEvent

from firebase_functions import core, db_fn


class TestDb(unittest.TestCase):
    """
    Tests for the db module.
    """

    def test_calls_init_function(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = mock.Mock(__name__="example_func")
        decorated_func = db_fn.on_value_created(reference="path")(func)

        event = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "id",
                "source": "source",
                "subject": "subject",
                "type": "type",
                "time": "2024-04-10T12:00:00.000Z",
                "instance": "instance",
                "ref": "ref",
                "firebasedatabasehost": "firebasedatabasehost",
                "location": "location",
                "authtype": "app_user",
                "authid": "auth-id",
            },
            data={"delta": "delta"},
        )

        decorated_func(event)

        func.assert_called_once()
        event_arg = func.call_args.args[0]
        self.assertIsNotNone(event_arg)
        self.assertEqual(event_arg.auth_type, "app_user")
        self.assertEqual(event_arg.auth_id, "auth-id")

        self.assertEqual(hello, "world")

    def test_missing_auth_context(self):
        func = mock.Mock(__name__="example_func_no_auth")
        decorated_func = db_fn.on_value_created(reference="path")(func)

        event = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "id",
                "source": "source",
                "subject": "subject",
                "type": "type",
                "time": "2024-04-10T12:00:00.000Z",
                "instance": "instance",
                "ref": "ref",
                "firebasedatabasehost": "firebasedatabasehost",
                "location": "location",
            },
            data={"delta": "delta"},
        )

        decorated_func(event)

        func.assert_called_once()
        event_arg = func.call_args.args[0]
        self.assertIsNotNone(event_arg)
        self.assertEqual(event_arg.auth_type, "unknown")
        self.assertIsNone(event_arg.auth_id)

    def test_written_event_parses_timestamp_without_microseconds(self):
        func = mock.Mock(__name__="example_func_no_microseconds")
        decorated_func = db_fn.on_value_written(reference="/items/{itemId}")(func)

        event = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "issue-257-repro",
                "source": "//firebase.test/projects/demo-test/instances/my-instance/refs/items/123",
                "subject": "refs/items/123",
                "type": "google.firebase.database.ref.v1.written",
                "time": "2025-10-30T21:15:51Z",
                "instance": "my-instance",
                "ref": "/items/123",
                "firebasedatabasehost": "my-instance.firebaseio.com",
                "location": "location",
            },
            data={
                "data": {"existing": True},
                "delta": {"updated": True},
            },
        )

        decorated_func(event)

        func.assert_called_once()
        event_arg = func.call_args.args[0]
        self.assertEqual(
            event_arg.time,
            dt.datetime(2025, 10, 30, 21, 15, 51, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(event_arg.data.after, {"existing": True, "updated": True})
        self.assertEqual(event_arg.params, {"itemId": "123"})
