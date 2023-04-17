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
"""Remote Config function tests."""
import unittest
from unittest.mock import MagicMock
from cloudevents.http import CloudEvent as _CloudEvent

from firebase_functions.remote_config_fn import (
    CloudEvent,
    ConfigUser,
    ConfigUpdateData,
    ConfigUpdateOrigin,
    ConfigUpdateType,
    on_config_updated,
    _config_handler,
)


class TestRemoteConfig(unittest.TestCase):
    """
    Remote Config function tests.
    """

    def test_on_config_updated_decorator(self):
        """
        Tests the on_config_updated decorator functionality by checking
        that the __firebase_endpoint__ attribute is set properly.
        """
        func = MagicMock()
        func.__name__ = "testfn"
        decorated_func = on_config_updated()(func)
        endpoint = getattr(decorated_func, "__firebase_endpoint__")
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertIsNotNone(endpoint.eventTrigger["eventType"])

    def test_config_handler(self):
        """
        Tests the _config_handler function, ensuring that it correctly processes
        the raw event and calls the user-provided function with a properly
        formatted CloudEvent instance.
        """
        func = MagicMock()
        raw_event = _CloudEvent(
            attributes={
                "specversion": "1.0",
                "type": "com.example.someevent",
                "source": "https://example.com/someevent",
                "id": "A234-1234-1234",
                "time": "2023-03-11T13:25:37.403Z",
            },
            data={
                "versionNumber": 42,
                "updateTime": "2023-03-11T13:25:37.403Z",
                "updateUser": {
                    "name": "John Doe",
                    "email": "johndoe@example.com",
                    "imageUrl": "https://example.com/image.jpg"
                },
                "description": "Test update",
                "updateOrigin": "CONSOLE",
                "updateType": "INCREMENTAL_UPDATE",
                "rollbackSource": 41
            })

        _config_handler(func, raw_event)

        func.assert_called_once()

        event_arg = func.call_args.args[0]
        self.assertIsInstance(event_arg, CloudEvent)
        self.assertIsInstance(event_arg.data, ConfigUpdateData)
        self.assertIsInstance(event_arg.data.update_user, ConfigUser)
        self.assertEqual(event_arg.data.version_number, 42)
        self.assertEqual(event_arg.data.update_origin,
                         ConfigUpdateOrigin.CONSOLE)
        self.assertEqual(event_arg.data.update_type,
                         ConfigUpdateType.INCREMENTAL_UPDATE)
        self.assertEqual(event_arg.data.rollback_source, 41)
