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
"""Functions to handle Tasks enqueued with Google Cloud Tasks."""

# pylint: disable=protected-access
import dataclasses as _dataclasses
import functools as _functools
import json as _json
import typing as _typing

from flask import Request, Response
from flask import jsonify as _jsonify
from flask import make_response as _make_response
from functions_framework import logging as _logging

import firebase_functions.core as _core
import firebase_functions.options as _options
import firebase_functions.private.util as _util
from firebase_functions.https_fn import CallableRequest, FunctionsErrorCode, HttpsError

_C = _typing.Callable[[CallableRequest[_typing.Any]], _typing.Any]
_C1 = _typing.Callable[[Request], Response]
_C2 = _typing.Callable[[CallableRequest[_typing.Any]], _typing.Any]


def _on_call_handler(func: _C2, request: Request) -> Response:
    try:
        if not _util.valid_on_call_request(request):
            _logging.error("Invalid request, unable to process.")
            raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")
        context: CallableRequest = CallableRequest(
            raw_request=request,
            data=_json.loads(request.data)["data"],
        )

        instance_id = request.headers.get("Firebase-Instance-ID-Token")
        if instance_id is not None:
            # Validating the token requires an http request, so we don't do it.
            # If the user wants to use it for something, it will be validated then.
            # Currently, the only real use case for this token is for sending
            # pushes with FCM. In that case, the FCM APIs will validate the token.
            context = _dataclasses.replace(
                context,
                instance_id_token=request.headers.get("Firebase-Instance-ID-Token"),
            )
        result = _core._with_init(func)(context)
        return _jsonify(result=result)
    # Disable broad exceptions lint since we want to handle all exceptions here
    # and wrap as an HttpsError.
    # pylint: disable=broad-except
    except Exception as err:
        if not isinstance(err, HttpsError):
            _logging.error("Unhandled error: %s", err)
            err = HttpsError(FunctionsErrorCode.INTERNAL, "INTERNAL")
        status = err._http_error_code.status
        return _make_response(_jsonify(error=err._as_dict()), status)


@_util.copy_func_kwargs(_options.TaskQueueOptions)
def on_task_dispatched(**kwargs) -> _typing.Callable[[_C], Response]:
    """
    Creates a handler for tasks sent to a Google Cloud Tasks queue.
    Requires a function that takes a CallableRequest.

    Example:

    .. code-block:: python

      @tasks.on_task_dispatched()
      def example(request: tasks.CallableRequest) -> Any:
          return "Hello World"

    :param \\*\\*kwargs: TaskQueueOptions options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.TaskQueueOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.https.CallableRequest` \\[
            :exc:`object` \\] \\], :exc:`object` \\]
            A function that takes a CallableRequest and returns an :exc:`object`.
    """
    options = _options.TaskQueueOptions(**kwargs)

    def on_task_dispatched_decorator(func: _C):
        @_functools.wraps(func)
        def on_task_dispatched_wrapped(request: Request) -> Response:
            return _on_call_handler(func, request)

        _util.set_func_endpoint_attr(
            on_task_dispatched_wrapped,
            options._endpoint(func_name=func.__name__),
        )
        _util.set_required_apis_attr(
            on_task_dispatched_wrapped,
            options._required_apis(),
        )
        return on_task_dispatched_wrapped

    return on_task_dispatched_decorator
