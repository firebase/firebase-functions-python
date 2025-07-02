"""
Tests for the db module.
"""

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
            },
            data={"delta": "delta"},
        )

        decorated_func(event)

        self.assertEqual(hello, "world")
