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
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, scheduler_fn


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
            schedule="* * * * *", timezone=scheduler_fn.Timezone(tz)
        )(example_func)
        endpoint = decorated_func.__firebase_endpoint__

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
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T12:00:00-07:00",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
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
                )
            )

    def test_on_schedule_call_with_z_suffix(self):
        """
        Tests to ensure that timestamps with 'Z' suffix are parsed correctly as UTC.
        """
        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T19:00:00Z",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)
            example_func.assert_called_once_with(
                scheduler_fn.ScheduledEvent(
                    job_name="example-job",
                    schedule_time=datetime(2023, 4, 13, 19, 0, 0, tzinfo=timezone.utc),
                )
            )

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
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(example_func.call_count, 1)
            self.assertIsNone(example_func.call_args[0][0].job_name)
            self.assertIsNotNone(example_func.call_args[0][0].schedule_time)
            self.assertIsNotNone(example_func.call_args[0][0].schedule_time.tzinfo)

    def test_on_schedule_call_with_exception(self):
        """
        Tests to ensure exceptions in the users handler are handled
        caught and returns a 500 status code.
        """

        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T12:00:00-07:00",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func", side_effect=Exception("Test exception"))
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.data, b"Test exception")

    def test_on_schedule_call_with_fractional_seconds(self):
        """
        Tests to ensure that timestamps with fractional seconds are parsed correctly.
        """
        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T19:00:00.123456Z",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)
            example_func.assert_called_once_with(
                scheduler_fn.ScheduledEvent(
                    job_name="example-job",
                    schedule_time=datetime(2023, 4, 13, 19, 0, 0, 123456, tzinfo=timezone.utc),
                )
            )

    def test_on_schedule_call_fallback_parsing(self):
        """
        Tests fallback parsing for formats that might fail fromisoformat
        but pass strptime (e.g., offset without colon).
        """
        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    # Offset without colon might fail fromisoformat in some versions
                    # but should pass strptime("%Y-%m-%dT%H:%M:%S%z")
                    "X-CloudScheduler-ScheduleTime": "2023-04-13T12:00:00-0700",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            response = decorated_func(mock_request)

            self.assertEqual(response.status_code, 200)

            # Create expected datetime with fixed offset -07:00
            tz = datetime.strptime("-0700", "%z").tzinfo
            expected_dt = datetime(2023, 4, 13, 12, 0, 0, tzinfo=tz)

            example_func.assert_called_once_with(
                scheduler_fn.ScheduledEvent(
                    job_name="example-job",
                    schedule_time=expected_dt,
                )
            )

    def test_on_schedule_call_invalid_timestamp(self):
        """
        Tests that invalid timestamps log an error and fallback to current time.
        """
        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder(
                headers={
                    "X-CloudScheduler-JobName": "example-job",
                    "X-CloudScheduler-ScheduleTime": "invalid-timestamp",
                }
            ).get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")

            with patch("firebase_functions.scheduler_fn._logging") as mock_logging:
                decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
                response = decorated_func(mock_request)

                self.assertEqual(response.status_code, 200)
                mock_logging.exception.assert_called_once()

                # Should have called with *some* time (current time), so we just check it's not None
                self.assertEqual(example_func.call_count, 1)
                called_event = example_func.call_args[0][0]
                self.assertEqual(called_event.job_name, "example-job")
                self.assertIsNotNone(called_event.schedule_time)
                self.assertIsNotNone(called_event.schedule_time.tzinfo)

    def test_calls_init(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        with Flask(__name__).test_request_context("/"):
            environ = EnvironBuilder().get_environ()
            mock_request = Request(environ)
            example_func = Mock(__name__="example_func")
            decorated_func = scheduler_fn.on_schedule(schedule="* * * * *")(example_func)
            decorated_func(mock_request)

            self.assertEqual("world", hello)
