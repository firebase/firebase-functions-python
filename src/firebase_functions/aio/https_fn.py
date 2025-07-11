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
"""Module for async functions that listen to HTTPS endpoints.
These can be raw web requests and Callable RPCs.
"""

import inspect as _inspect
import typing as _typing

# Import the shared implementation and types from the sync module
from firebase_functions.https_fn import (
    CallableRequest,
    FunctionsErrorCode,
    HttpsError,
    _create_on_call_decorator,
    _create_on_request_decorator,
)
from firebase_functions.options import HttpsOptions
from firebase_functions.private import util as _util

# Type stubs for Starlette types (to avoid hard dependency)
# In production, these would be actual imports from starlette
if _typing.TYPE_CHECKING:
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse
else:
    # Runtime placeholder types
    StarletteRequest = _typing.Any
    StarletteResponse = _typing.Any

# Type aliases for async handlers
_AsyncC1 = _typing.Callable[[StarletteRequest], _typing.Awaitable[StarletteResponse]]
_AsyncC2 = _typing.Callable[[CallableRequest[_typing.Any]], _typing.Awaitable[_typing.Any]]


@_util.copy_func_kwargs(HttpsOptions)
def on_request(**kwargs) -> _typing.Callable[[_AsyncC1], _AsyncC1]:
    """
    Handler which handles async HTTPS requests.
    Requires an async function that takes a Starlette ``Request`` and returns a ``Response``.

    Example:

    .. code-block:: python

      from firebase_functions.aio import https_fn

      @https_fn.on_request()
      async def example(request) -> Response:
          await some_async_operation()
          return Response("Hello async world!")

    :param \\*\\*kwargs: Https options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.HttpsOptions`
    :rtype: :exc:`typing.Callable` \\[ \\[ :exc:`starlette.requests.Request` \\],
            :exc:`typing.Awaitable` \\[ :exc:`starlette.responses.Response` \\] \\]
            An async function that takes a Starlette Request and returns a Response.
    """
    options = HttpsOptions(**kwargs)

    def on_request_inner_decorator(func: _AsyncC1) -> _AsyncC1:
        if not _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"aio.https_fn.on_request() requires an async function, "
                f"but {func.__name__} is not async. "
                f"Use @https_fn.on_request() for synchronous functions."
            )
        return _typing.cast(_AsyncC1, _create_on_request_decorator(func, options, asgi=True))

    return on_request_inner_decorator


@_util.copy_func_kwargs(HttpsOptions)
def on_call(**kwargs) -> _typing.Callable[[_AsyncC2], _AsyncC2]:
    """
    Declares an async callable method for clients to call using a Firebase SDK.
    Requires an async function that takes a ``CallableRequest``.

    Example:

    .. code-block:: python

      from firebase_functions.aio import https_fn

      @https_fn.on_call()
      async def example(request: CallableRequest) -> Any:
          await some_async_operation()
          return {"message": "Hello async world!"}

    :param \\*\\*kwargs: Https options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.HttpsOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.https.CallableRequest` \\[
            :exc:`object` \\] \\], :exc:`typing.Awaitable` \\[ :exc:`object` \\] \\]
            An async function that takes a ``CallableRequest`` and returns an object.
    """
    options = HttpsOptions(**kwargs)

    def on_call_inner_decorator(func: _AsyncC2) -> _AsyncC2:
        if not _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"aio.https_fn.on_call() requires an async function, "
                f"but {func.__name__} is not async. "
                f"Use @https_fn.on_call() for synchronous functions."
            )
        return _typing.cast(_AsyncC2, _create_on_call_decorator(func, options, asgi=True))

    return on_call_inner_decorator


# Re-export common types and exceptions so users don't need to import from both modules
__all__ = [
    "on_request",
    "on_call",
    "HttpsError",
    "FunctionsErrorCode",
    "CallableRequest",
]
