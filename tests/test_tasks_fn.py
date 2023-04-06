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
"""Task Queue function tests."""
import unittest

from unittest.mock import MagicMock
from flask import Flask, Request
from werkzeug.test import EnvironBuilder
from firebase_functions.tasks_fn import on_task_dispatched, CallableRequest


class TestTasks(unittest.TestCase):
    """
    Task Queue function tests.
    """

    def test_on_task_dispatched_decorator(self):
        """
        Tests the on_task_dispatched decorator functionality by checking
        that the __firebase_endpoint__ attribute is set properly.
        """

        func = MagicMock()
        func.__name__ = "testfn"
        decorated_func = on_task_dispatched()(func)
        endpoint = getattr(decorated_func, "__firebase_endpoint__")
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.taskQueueTrigger)

    def test_task_handler(self):
        """
        Test the proper execution of the task handler created by the on_task_dispatched
        decorator. This test will create a Flask app, apply the on_task_dispatched
        decorator to the example function, inject a request, and then ensure that a
        correct response is generated.
        """
        app = Flask(__name__)

        @on_task_dispatched()
        def example(request: CallableRequest[object]) -> str:
            self.assertEqual(request.data, {"test": "value"})
            return "Hello World"

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {
                        "test": "value"
                    },
                },
            ).get_environ()
            request = Request(environ)
            response = example(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_data(as_text=True),
                '{"result":"Hello World"}\n',
            )
