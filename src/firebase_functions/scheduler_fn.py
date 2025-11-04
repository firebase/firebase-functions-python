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
"""Cloud functions to handle Schedule triggers."""

import dataclasses as _dataclasses
import datetime as _dt
import functools as _functools
import typing as _typing
from datetime import timezone as _timezone

from flask import (
    Request as _Request,
)
from flask import (
    Response as _Response,
)
from flask import (
    make_response as _make_response,
)
from functions_framework import logging as _logging

import firebase_functions.options as _options
import firebase_functions.private.util as _util
from firebase_functions.core import _with_init

# Re-export Timezone from options module so users can import it directly from scheduler_fn
# This provides a more convenient API: from firebase_functions.scheduler_fn import Timezone
from firebase_functions.options import Timezone  # noqa: F401


@_dataclasses.dataclass(frozen=True)
class ScheduledEvent:
    """
    A ``ScheduleEvent`` that is passed to the function handler.
    """

    job_name: str | None
    """
    The Cloud Scheduler job name.
    Populated via the ``X-CloudScheduler-JobName`` header.
    If invoked manually, this field is `None`.
    """

    schedule_time: _dt.datetime
    """
    For Cloud Scheduler jobs specified in the unix-cron format,
    this is the job schedule time in RFC3339 UTC "Zulu" format.
    Populated via the ``X-CloudScheduler-ScheduleTime`` header.

    If the schedule is manually triggered, this field is
    the function execution time.
    """


_C = _typing.Callable[[ScheduledEvent], None]


@_util.copy_func_kwargs(_options.ScheduleOptions)
def on_schedule(**kwargs) -> _typing.Callable[[_C], _Response]:
    """
    Creates a handler for tasks sent to a Google Cloud Tasks queue.
    Requires a function that takes a ``CallableRequest``.

    Example:

    .. code-block:: python

      from firebase_functions import scheduler_fn


      @scheduler_fn.on_schedule(
          schedule="* * * * *",
          timezone=scheduler_fn.Timezone("America/Los_Angeles"),
      )
      def example(event: scheduler_fn.ScheduledEvent) -> None:
          print(event.job_name)
          print(event.schedule_time)


    :param \\*\\*kwargs: `ScheduleOptions` options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.ScheduleOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.schedule_fn.ScheduledEvent` \\], :exc:`None` \\]
            A function that takes a ``ScheduledEvent`` and returns nothing.
    """
    options = _options.ScheduleOptions(**kwargs)

    def on_schedule_decorator(func: _C):
        @_functools.wraps(func)
        def on_schedule_wrapped(request: _Request) -> _Response:
            schedule_time: _dt.datetime
            schedule_time_str = request.headers.get("X-CloudScheduler-ScheduleTime")
            if schedule_time_str is None:
                schedule_time = _dt.datetime.now(_timezone.utc)
            else:
                try:
                    # Try to parse with the stdlib which supports fractional
                    # seconds and offsets in Python 3.11+ via fromisoformat.
                    # Normalize RFC3339 'Z' to '+00:00' for fromisoformat.
                    iso_str = schedule_time_str
                    if iso_str.endswith("Z"):
                        iso_str = iso_str[:-1] + "+00:00"
                    schedule_time = _dt.datetime.fromisoformat(iso_str)
                except ValueError:
                    # Fallback to strict parsing without fractional seconds
                    try:
                        schedule_time = _dt.datetime.strptime(
                            schedule_time_str,
                            "%Y-%m-%dT%H:%M:%S%z",
                        )
                    except ValueError as e:
                        # If all parsing fails, log and use current UTC time
                        _logging.exception(e)
                        schedule_time = _dt.datetime.now(_timezone.utc)
            event = ScheduledEvent(
                job_name=request.headers.get("X-CloudScheduler-JobName"),
                schedule_time=schedule_time,
            )
            try:
                _with_init(func)(event)
                return _make_response()
            # Disable broad exceptions lint since we want to handle all exceptions.
            # pylint: disable=broad-except
            except Exception as exception:
                _logging.exception(exception)
                return _make_response(str(exception), 500)

        _util.set_func_endpoint_attr(
            on_schedule_wrapped,
            # pylint: disable=protected-access
            options._endpoint(func_name=func.__name__),
        )
        _util.set_required_apis_attr(
            on_schedule_wrapped,
            # pylint: disable=protected-access
            options._required_apis(),
        )
        return on_schedule_wrapped

    return on_schedule_decorator
