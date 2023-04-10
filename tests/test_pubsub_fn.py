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
"""PubSub function tests."""
import unittest
import datetime as _dt
from unittest.mock import MagicMock
from cloudevents.http import CloudEvent as _CloudEvent

from firebase_functions.pubsub_fn import (
    Message,
    MessagePublishedData,
    on_message_published,
    _message_handler,
    CloudEvent,
)


class TestPubSub(unittest.TestCase):
    """
    PubSub function tests.
    """

    def test_on_message_published_decorator(self):
        """
        Tests the on_message_published decorator functionality by checking that
        the _endpoint attribute is set properly.
        """
        func = MagicMock()
        func.__name__ = "testfn"
        decorated_func = on_message_published(topic="hello-world")(func)
        endpoint = getattr(decorated_func, "__firebase_endpoint__")
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertIsNotNone(endpoint.eventTrigger["eventType"])
        self.assertEqual("hello-world",
                         endpoint.eventTrigger["eventFilters"]["topic"])

    def test_message_handler(self):
        """
        Tests the _message_handler function, ensuring that it correctly processes
        the raw event and calls the user-provided function with a properly
        formatted CloudEvent instance.
        """
        func = MagicMock()
        raw_event = _CloudEvent(
            attributes={
                "id": "test-message",
                "source": "https://example.com/pubsub",
                "specversion": "1.0",
                "time": "2023-03-11T13:25:37.403Z",
                "type": "com.example.pubsub.message",
            },
            data={
                "message": {
                    "attributes": {
                        "key": "value"
                    },
                    # {"test": "value"}
                    "data": "eyJ0ZXN0IjogInZhbHVlIn0=",
                    "message_id": "message-id-123",
                    "publish_time": "2023-03-11T13:25:37.403Z",
                },
                "subscription": "my-subscription",
            },
        )

        _message_handler(func, raw_event)
        func.assert_called_once()
        event_arg = func.call_args.args[0]
        self.assertIsInstance(event_arg, CloudEvent)
        self.assertIsInstance(event_arg.data, MessagePublishedData)
        self.assertIsInstance(event_arg.data.message, Message)
        self.assertEqual(event_arg.data.message.message_id, "message-id-123")
        self.assertEqual(
            event_arg.data.message.publish_time,
            _dt.datetime.strptime(
                "2023-03-11T13:25:37.403Z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
            ))
        self.assertDictEqual(event_arg.data.message.attributes,
                             {"key": "value"})
        self.assertEqual(event_arg.data.message.data,
                         "eyJ0ZXN0IjogInZhbHVlIn0=")
        self.assertIsNone(event_arg.data.message.ordering_key)
        self.assertEqual(event_arg.data.subscription, "my-subscription")
