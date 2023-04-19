# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Eventarc trigger function tests."""
import unittest
from unittest.mock import Mock
from cloudevents.http import CloudEvent as _CloudEvent
from firebase_functions.core import CloudEvent
from firebase_functions.eventarc_fn import on_custom_event_published


class TestEventarcFn(unittest.TestCase):
    """
    Test Eventarc trigger functions.
    """

    def test_on_custom_event_published_decorator(self):
        """
        Tests the on_custom_event_published decorator functionality by checking
        that the __firebase_endpoint__ attribute is set properly.
        """
        func = Mock(__name__="example_func")

        decorated_func = on_custom_event_published(
            event_type="firebase.extensions.storage-resize-images.v1.complete",
        )(func)

        endpoint = getattr(decorated_func, "__firebase_endpoint__")
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertEqual(
            endpoint.eventTrigger["eventType"],
            "firebase.extensions.storage-resize-images.v1.complete",
        )

    def test_on_custom_event_published_wrapped(self):
        """
        Tests the wrapped function created by the on_custom_event_published
        decorator, ensuring that it correctly processes the raw event and calls
        the user-provided function with a properly formatted CloudEvent instance.
        """
        func = Mock(__name__="example_func")
        raw_event = _CloudEvent(
            attributes={
                "specversion": "1.0",
                "type": "firebase.extensions.storage-resize-images.v1.complete",
                "source": "https://example.com/testevent",
                "id": "1234567890",
                "subject": "test_subject",
                "time": "2023-03-11T13:25:37.403Z",
            },
            data={
                "some_key": "some_value",
            },
        )

        decorated_func = on_custom_event_published(
            event_type="firebase.extensions.storage-resize-images.v1.complete",
        )(func)

        decorated_func(raw_event)

        func.assert_called_once()

        event_arg = func.call_args.args[0]
        self.assertIsInstance(event_arg, CloudEvent)
        self.assertEqual(event_arg.data, {"some_key": "some_value"})
        self.assertEqual(event_arg.id, "1234567890")
        self.assertEqual(event_arg.source, "https://example.com/testevent")
        self.assertEqual(event_arg.specversion, "1.0")
        self.assertEqual(event_arg.subject, "test_subject")
        self.assertEqual(
            event_arg.type,
            "firebase.extensions.storage-resize-images.v1.complete",
        )
