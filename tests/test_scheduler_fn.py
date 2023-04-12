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
"""Scheduler function tests."""
import unittest
from unittest.mock import Mock
from datetime import datetime
from flask import Request, Flask
from werkzeug.test import EnvironBuilder
from firebase_functions import scheduler_fn


class TestScheduler(unittest.TestCase):
    """
    Scheduler function tests.
    """

    def test_on_schedule_decorator(self):
        """
        Tests the on_schedule decorator functionality by checking
        that the __firebase_endpoint__ attribute is set properly.
        """

        schedule = "* * * * *"
        tz = "America/Los_Angeles"
        example_func = Mock(__name__="example_func")
        decorated_func = scheduler_fn.on_schedule(
            schedule="* * * * *",
            timezone=scheduler_fn.Timezone(tz))(example_func)
        endpoint = getattr(decorated_func, "__firebase_endpoint__")

        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.scheduleTrigger)
        self.assertEqual(endpoint.scheduleTrigger.get("schedule"), schedule)
        self.assertEqual(endpoint.scheduleTrigger.get("timeZone"), tz)

    def test_on_schedule_call(self):
        """
        Tests to ensure the decorated function is called correctly
        with appropriate ScheduledEvent object and returns a 200
        status code if successful.
        """

        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T12:00:00-07:00"
                }).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(
                schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)
            example_func.assert_called_once_with(
                scheduler_fn.ScheduledEvent(
                    job_name="example-job",
                    schedule_time=datetime(
                        2023,
                        4,
                        13,
                        12,
                        0,
                        tzinfo=scheduler_fn.Timezone("America/Los_Angeles"),
                    ),
                ))

    def test_on_schedule_call_with_no_headers(self):
        """
        Tests to ensure that if the function is called manually
        then the ScheduledEvent object is populated with the
        current time and the job_name is None.
        """

        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder().get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(
                schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(example_func.call_count, 1)
            self.assertIsNone(example_func.call_args[0][0].job_name)
            self.assertIsNotNone(example_func.call_args[0][0].schedule_time)

    def test_on_schedule_call_with_exception(self):
        """
        Tests to ensure exceptions in the users handler are handled
        caught and returns a 500 status code.
        """

        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T12:00:00-07:00"
                }).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func",
                                side_effect=Exception("Test exception"))
            decorated_func = scheduler_fn.on_schedule(
                schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.data, b"Test exception")
