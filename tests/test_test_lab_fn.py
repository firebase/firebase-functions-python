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
"""Test Lab function tests."""
import unittest
from unittest.mock import MagicMock
from cloudevents.http import CloudEvent as _CloudEvent

from firebase_functions.test_lab_fn import (
    CloudEvent,
    TestMatrixCompletedData,
    TestState,
    OutcomeSummary,
    ResultStorage,
    ClientInfo,
    on_test_matrix_completed,
    _event_handler,
)


class TestTestLab(unittest.TestCase):
    """
    Test Lab function tests.
    """

    def test_on_test_matrix_completed_decorator(self):
        """
        Tests the on_test_matrix_completed decorator functionality by checking
        that the __firebase_endpoint__ attribute is set properly.
        """
        func = MagicMock()
        func.__name__ = "testfn"
        decorated_func = on_test_matrix_completed()(func)
        endpoint = getattr(decorated_func, "__firebase_endpoint__")
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertIsNotNone(endpoint.eventTrigger["eventType"])

    def test_event_handler(self):
        """
        Tests the _event_handler function, ensuring that it correctly processes
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
                "createTime": "2023-03-11T13:25:37.403Z",
                "state": "FINISHED",
                "invalidMatrixDetails": "Some details",
                "outcomeSummary": "SUCCESS",
                "resultStorage": {
                    "toolResultsHistory":
                        "projects/123/histories/456",
                    "resultsUri":
                        "https://example.com/results",
                    "gcsPath":
                        "gs://bucket/path/to/somewhere",
                    "toolResultsExecution":
                        "projects/123/histories/456/executions/789",
                },
                "clientInfo": {
                    "client": "gcloud",
                },
                "testMatrixId": "testmatrix-123",
            })

        _event_handler(func, raw_event)

        func.assert_called_once()

        event_arg = func.call_args.args[0]
        self.assertIsInstance(event_arg, CloudEvent)
        self.assertIsInstance(event_arg.data, TestMatrixCompletedData)
        self.assertIsInstance(event_arg.data.result_storage, ResultStorage)
        self.assertIsInstance(event_arg.data.client_info, ClientInfo)
        self.assertEqual(event_arg.data.state, TestState.FINISHED)
        self.assertEqual(event_arg.data.outcome_summary, OutcomeSummary.SUCCESS)
        self.assertEqual(event_arg.data.test_matrix_id, "testmatrix-123")
