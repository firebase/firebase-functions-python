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
"""Cloud functions to handle Tasks enqueued with Google Cloud Tasks."""

# pylint: disable=protected-access
import typing as _typing
import functools as _functools

from flask import Request, Response

import firebase_functions.options as _options
import firebase_functions.private.util as _util
from firebase_functions.https import CallableRequest, _on_call_handler

_C = _typing.Callable[[CallableRequest[_typing.Any]], _typing.Any]


@_util.copy_func_kwargs(_options.TaskQueueOptions)
def on_task_dipached(**kwargs) -> _typing.Callable[[_C], Response]:
    """
    A handler for tasks.

    Example::
      @tasks.on_task_dipached(retry_limit=5)
      def on_task_dipached_example(req: tasks.CallableRequest):
        pass

    """
    options = _options.TaskQueueOptions(**kwargs)

    def on_task_dipached_decorator(func: _C):

        @_functools.wraps(func)
        def on_task_dipached_wrapped(request: Request) -> Response:
            return _on_call_handler(func, request)

        _util.set_func_endpoint_attr(
            on_task_dipached_wrapped,
            options._endpoint(func_name=func.__name__),
        )
        return on_task_dipached_wrapped

    return on_task_dipached_decorator
