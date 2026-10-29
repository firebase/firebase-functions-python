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

import datetime as _dt
import unittest
from unittest.mock import MagicMock

from cloudevents.http import CloudEvent as _CloudEvent

from firebase_functions import core
from firebase_functions.pubsub_fn import (
    CloudEvent,
    Message,
    MessagePublishedData,
    _message_handler,
    on_message_published,
)


def _raw_event(message: dict, time: str = "2023-03-11T13:25:37.403Z") -> _CloudEvent:
    return _CloudEvent(
        attributes={
            "id": "test-message",
            "source": "https://example.com/pubsub",
            "specversion": "1.0",
            "time": time,
            "type": "com.example.pubsub.message",
        },
        data={
            "message": {
                "message_id": "message-id-123",
                "publish_time": time,
                **message,
            },
            "subscription": "my-subscription",
        },
    )


def _handled_message(message: dict) -> Message:
    func = MagicMock()
    _message_handler(func, _raw_event(message))
    func.assert_called_once()
    return func.call_args.args[0].data.message


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
        endpoint = decorated_func.__firebase_endpoint__
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertIsNotNone(endpoint.eventTrigger["eventType"])
        self.assertEqual("hello-world", endpoint.eventTrigger["eventFilters"]["topic"])

    def test_message_handler(self):
        """
        Tests the _message_handler function, ensuring that it correctly processes
        the raw event and calls the user-provided function with a properly
        formatted CloudEvent instance.
        """
        func = MagicMock()
        raw_event = _raw_event(
            {
                "attributes": {"key": "value"},
                # {"test": "value"}
                "data": "eyJ0ZXN0IjogInZhbHVlIn0=",
            }
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
            ),
        )
        self.assertDictEqual(event_arg.data.message.attributes, {"key": "value"})
        self.assertEqual(event_arg.data.message.data, "eyJ0ZXN0IjogInZhbHVlIn0=")
        self.assertIsNone(event_arg.data.message.ordering_key)
        self.assertEqual(event_arg.data.subscription, "my-subscription")

    def test_calls_init(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = MagicMock()
        raw_event = _raw_event({"data": "eyJ0ZXN0IjogInZhbHVlIn0="})

        _message_handler(func, raw_event)

        self.assertEqual("world", hello)

    def test_datetime_without_mircroseconds_doesnt_throw(self):
        time = "2023-03-11T13:25:37Z"
        raw_event = _raw_event({"data": "eyJ0ZXN0IjogInZhbHVlIn0="}, time=time)
        try:
            _message_handler(lambda _: None, raw_event)
        # pylint: disable=broad-except
        except Exception:
            self.fail("Datetime without microseconds should not throw an exception")


class TestPubSubMessageData(unittest.TestCase):
    def test_message_without_data_reaches_handler_with_none(self):
        message = _handled_message({"attributes": {"key": "value"}})
        self.assertIsNone(message.data)
        self.assertIsNone(message.json)
        self.assertEqual(message.attributes, {"key": "value"})
        self.assertEqual(message.message_id, "message-id-123")

    def test_message_with_data_decodes_json(self):
        # base64 of '{"test": "value"}'
        message = _handled_message({"data": "eyJ0ZXN0IjogInZhbHVlIn0="})
        self.assertEqual(message.data, "eyJ0ZXN0IjogInZhbHVlIn0=")
        self.assertEqual(message.json, {"test": "value"})
        self.assertEqual(message.attributes, {})

    def test_message_with_empty_string_data_reaches_handler_with_none(self):
        message = _handled_message({"data": ""})
        self.assertIsNone(message.data)
        self.assertIsNone(message.json)

    def test_message_with_invalid_data_json_raises(self):
        # base64 of "not json"
        message = _handled_message({"data": "bm90IGpzb24="})
        with self.assertRaisesRegex(ValueError, "^Unable to parse Pub/Sub message data as JSON: "):
            _ = message.json

    def test_message_with_ordering_key_keeps_it(self):
        message = _handled_message({"data": "eyJ0ZXN0IjogInZhbHVlIn0=", "orderingKey": "abc"})
        self.assertEqual(message.ordering_key, "abc")

    def test_message_built_directly_defaults_data_and_ordering_key_to_none(self):
        message = Message(
            message_id="message-id-123",
            publish_time=_dt.datetime(2023, 3, 11, tzinfo=_dt.timezone.utc),
            attributes={},
        )
        self.assertIsNone(message.data)
        self.assertIsNone(message.ordering_key)
        self.assertIsNone(message.json)

    def test_publish_time_is_timezone_aware_datetime(self):
        message = _handled_message({"data": "eyJ0ZXN0IjogInZhbHVlIn0="})
        self.assertIsInstance(message.publish_time, _dt.datetime)
        self.assertEqual(
            message.publish_time,
            _dt.datetime(2023, 3, 11, 13, 25, 37, 403000, tzinfo=_dt.timezone.utc),
        )
        self.assertEqual(message.publish_time.utcoffset(), _dt.timedelta(0))
