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
"""Module for functions that listen to HTTPS endpoints.
These can be raw web requests and Callable RPCs.
"""

# pylint: disable=protected-access
import dataclasses as _dataclasses
import enum as _enum
import functools as _functools
import inspect as _inspect
import json as _json
import typing as _typing

import typing_extensions as _typing_extensions
from flask import Request, Response
from flask import jsonify as _jsonify
from flask import make_response as _make_response
from flask_cors import cross_origin as _cross_origin
from functions_framework import logging as _logging

import firebase_functions.core as _core
import firebase_functions.private.util as _util
from firebase_functions.options import _GLOBAL_OPTIONS, CorsOptions, HttpsOptions


class FunctionsErrorCode(str, _enum.Enum):
    """
    The set of Cloud Functions status codes. The codes are the same as the
    ones exposed by gRPC here:
    https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
    """

    OK = "ok"

    CANCELLED = "cancelled"
    """
    The operation was cancelled (typically by the caller).
    """

    UNKNOWN = "unknown"
    """
    Unknown error or an error from a different error domain.
    """

    INVALID_ARGUMENT = "invalid-argument"
    """
    Client specified an invalid argument. Note that this
    differs from `failed-precondition`. `invalid-argument` indicates
    arguments that are problematic regardless of the state of the system
    (such as an invalid field name).
    """

    DEADLINE_EXCEEDED = "deadline-exceeded"
    """
    Deadline expired before operation could complete.
    For operations that change the state of the system, this error may be
    returned even if the operation has completed successfully. For example,
    a successful response from a server could have been delayed long enough
    for the deadline to expire.
    """

    NOT_FOUND = "not-found"
    """
    Some requested document was not found.
    """

    ALREADY_EXISTS = "already-exists"
    """
    Some document that we attempted to create already
    exists.
    """

    PERMISSION_DENIED = "permission-denied"
    """
    The caller does not have permission to execute the
    specified operation.
    """

    UNAUTHENTICATED = "unauthenticated"
    """
    The request does not have valid authentication
    credentials for the operation.
    """

    RESOURCE_EXHAUSTED = "resource-exhausted"
    """
    Some resource has been exhausted, perhaps a
    per-user quota, or perhaps the entire file system is out of space.
    """

    FAILED_PRECONDITION = "failed-precondition"
    """
    Operation was rejected because the system is not
    in a state required for the operation's execution.
    """

    ABORTED = "aborted"
    """
    The operation was aborted, typically due to a concurrency
    issue like transaction aborts, etc.
    """

    OUT_OF_RANGE = "out-of-range"
    """
    Operation was attempted past the valid range.
    """

    UNIMPLEMENTED = "unimplemented"
    """
    Operation is not implemented or not supported/enabled.
    """

    INTERNAL = "internal"
    """
    Internal errors. Means some invariants expected by the
    underlying system have been broken. If you see one of these errors,
    something is severely broken.
    """

    UNAVAILABLE = "unavailable"
    """
    The service is currently unavailable. This is most likely
    a transient condition and may be corrected by retrying with a backoff.
    """

    DATA_LOSS = "data-loss"
    """
    Unrecoverable data loss or corruption.
    """

    def __str__(self) -> str:
        return self.value


class _CanonicalErrorCodeName(str, _enum.Enum):
    """The canonical error code name for a given error code."""

    OK = "OK"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    FAILED_PRECONDITION = "FAILED_PRECONDITION"
    ABORTED = "ABORTED"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNIMPLEMENTED = "UNIMPLEMENTED"
    INTERNAL = "INTERNAL"
    UNAVAILABLE = "UNAVAILABLE"
    DATA_LOSS = "DATA_LOSS"

    def __str__(self) -> str:
        return self.value


@_dataclasses.dataclass(frozen=True)
class _HttpErrorCode:
    """
    A standard error code that will be returned to the client. This also
    determines the HTTP status code of the response, as defined in code.proto.
    """

    canonical_name: _CanonicalErrorCodeName
    status: int


_error_code_map = {
    FunctionsErrorCode.OK: _HttpErrorCode(_CanonicalErrorCodeName.OK, 200),
    FunctionsErrorCode.CANCELLED: _HttpErrorCode(_CanonicalErrorCodeName.CANCELLED, 499),
    FunctionsErrorCode.UNKNOWN: _HttpErrorCode(_CanonicalErrorCodeName.UNKNOWN, 500),
    FunctionsErrorCode.INVALID_ARGUMENT: _HttpErrorCode(
        _CanonicalErrorCodeName.INVALID_ARGUMENT, 400
    ),
    FunctionsErrorCode.DEADLINE_EXCEEDED: _HttpErrorCode(
        _CanonicalErrorCodeName.DEADLINE_EXCEEDED, 504
    ),
    FunctionsErrorCode.NOT_FOUND: _HttpErrorCode(_CanonicalErrorCodeName.NOT_FOUND, 404),
    FunctionsErrorCode.ALREADY_EXISTS: _HttpErrorCode(_CanonicalErrorCodeName.ALREADY_EXISTS, 409),
    FunctionsErrorCode.PERMISSION_DENIED: _HttpErrorCode(
        _CanonicalErrorCodeName.PERMISSION_DENIED, 403
    ),
    FunctionsErrorCode.UNAUTHENTICATED: _HttpErrorCode(
        _CanonicalErrorCodeName.UNAUTHENTICATED, 401
    ),
    FunctionsErrorCode.RESOURCE_EXHAUSTED: _HttpErrorCode(
        _CanonicalErrorCodeName.RESOURCE_EXHAUSTED, 429
    ),
    FunctionsErrorCode.FAILED_PRECONDITION: _HttpErrorCode(
        _CanonicalErrorCodeName.FAILED_PRECONDITION, 400
    ),
    FunctionsErrorCode.ABORTED: _HttpErrorCode(_CanonicalErrorCodeName.ABORTED, 409),
    FunctionsErrorCode.OUT_OF_RANGE: _HttpErrorCode(_CanonicalErrorCodeName.OUT_OF_RANGE, 400),
    FunctionsErrorCode.UNIMPLEMENTED: _HttpErrorCode(_CanonicalErrorCodeName.UNIMPLEMENTED, 501),
    FunctionsErrorCode.INTERNAL: _HttpErrorCode(_CanonicalErrorCodeName.INTERNAL, 500),
    FunctionsErrorCode.UNAVAILABLE: _HttpErrorCode(_CanonicalErrorCodeName.UNAVAILABLE, 503),
    FunctionsErrorCode.DATA_LOSS: _HttpErrorCode(_CanonicalErrorCodeName.DATA_LOSS, 500),
}
"""
Standard error codes and HTTP statuses for different ways a request can fail,
as defined by:
https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto.
This map is used primarily to convert from a client error code string to
to the HTTP format error code string and status, and make sure it's in the
supported set.
"""


class _HttpErrorWireFormat(_typing.TypedDict):
    details: _typing_extensions.NotRequired[_typing.Any]
    status: str
    message: str


class HttpsError(Exception):
    """
    An explicit error that can be thrown from a handler to send an error to the
    client that called the function.
    """

    code: FunctionsErrorCode
    """
    A standard error code that will be returned to the client. This also
    determines the HTTP status code of the response.
    """

    details: _typing.Any | None = None
    """
    Extra data to be converted to JSON and included in the error response.
    """

    _http_error_code: _HttpErrorCode
    """
    A wire format representation of a provided error code.
    """

    def __init__(
        self,
        code: FunctionsErrorCode,
        message: str,
        details: _typing.Any | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details

        if code not in _error_code_map:
            raise ValueError(f"Unknown error code: ${code}.")

        self._http_error_code = _error_code_map[code]

        super().__init__()

    def _as_dict(self) -> _HttpErrorWireFormat:
        if self.details is None:
            return {
                "status": self._http_error_code.canonical_name.value,
                "message": self.message,
            }

        return {
            "details": self.details,
            "status": self._http_error_code.canonical_name,
            "message": self.message,
        }


@_dataclasses.dataclass(frozen=True)
class AuthData:
    """
    The interface for Auth tokens verified in Callable functions
    """

    uid: str | None
    """
    User ID of the ID token.
    """

    token: dict[str, _typing.Any]
    """
    The ID token's decoded claims.
    """


@_dataclasses.dataclass(frozen=True)
class AppCheckData:
    """
    The interface for AppCheck tokens verified in Callable functions
    """

    app_id: str
    """
    The App ID corresponding to the App the App Check token belonged to.
    This value is not actually one of the JWT token claims. It is added as a
    convenience, and is set as the value of the token `sub` property.
    """

    token: dict[str, _typing.Any]
    """
    The token's decoded claims.
    """


@_dataclasses.dataclass(frozen=True)
class CallableRequest(_typing.Generic[_core.T]):
    """
    The request used to call a callable function.
    """

    data: _core.T
    """
    The parameters used by a client when calling this function.
    """

    raw_request: Request
    """
    The raw request handled by the callable.
    """

    app: AppCheckData | None = None
    """
    The result of decoding and verifying a Firebase AppCheck token.
    """

    auth: AuthData | None = None
    """"
    The result of decoding and verifying a Firebase Auth ID token.
    """

    instance_id_token: str | None = None
    """
    An unverified token for a Firebase Instance ID.
    """


_C1 = _typing.Callable[[Request], Response]
_C2 = _typing.Callable[[CallableRequest[_typing.Any]], _typing.Any]


def _validate_on_call_request_headers(method: str, headers: dict) -> None:
    """Validate method and headers for on_call requests."""
    if method != "POST":
        _logging.warning("Request has invalid method. %s", method)
        raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")

    # Try both lowercase and capitalized versions for compatibility
    content_type = headers.get("content-type", "") or headers.get("Content-Type", "")
    if not content_type.startswith("application/json"):
        _logging.warning("Request has invalid content type. %s", content_type)
        raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")


def _process_on_call_request_body(
    raw_request: _typing.Any,
    body_bytes: bytes,
    headers: dict,
    method: str,
    enforce_app_check: bool,
) -> CallableRequest:
    """Process on_call request after body is read. Shared between sync/async."""
    # Validate headers/method
    _validate_on_call_request_headers(method, headers)

    # Parse and validate JSON
    try:
        json_data = _json.loads(body_bytes)
    except _json.JSONDecodeError:
        _logging.error("Request body is not valid JSON")
        raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request") from None

    if "data" not in json_data:
        _logging.warning("Request body is missing data.")
        raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")

    # Create mock request for token checking
    class HeadersAdapter:
        def __init__(self, headers):
            self.headers = headers

    mock_request = HeadersAdapter(headers)
    token_status = _util.on_call_check_tokens(mock_request)  # type: ignore

    # Validate tokens
    if token_status.auth == _util.OnCallTokenState.INVALID:
        raise HttpsError(FunctionsErrorCode.UNAUTHENTICATED, "Unauthenticated")

    if enforce_app_check and token_status.app in (
        _util.OnCallTokenState.MISSING,
        _util.OnCallTokenState.INVALID,
    ):
        raise HttpsError(FunctionsErrorCode.UNAUTHENTICATED, "Unauthenticated")

    # Build context
    context = CallableRequest(raw_request=raw_request, data=json_data["data"])

    # Add app check data
    if token_status.app == _util.OnCallTokenState.VALID and token_status.app_token is not None:
        context = _dataclasses.replace(
            context,
            app=AppCheckData(token_status.app_token["sub"], token_status.app_token),
        )

    # Add auth data
    if token_status.auth_token is not None:
        context = _dataclasses.replace(
            context,
            auth=AuthData(
                token_status.auth_token["uid"] if "uid" in token_status.auth_token else None,
                token_status.auth_token,
            ),
        )

    # Add instance ID (try both cases)
    instance_id = headers.get("firebase-instance-id-token") or headers.get("Firebase-Instance-ID-Token")
    if instance_id is not None:
        context = _dataclasses.replace(context, instance_id_token=instance_id)

    return context


def _format_on_call_response(result: _typing.Any) -> dict:
    """Format the result for on_call response."""
    return {"result": result}


def _format_on_call_error(err: Exception) -> tuple[dict, int]:
    """Format error for on_call response."""
    if not isinstance(err, HttpsError):
        _logging.error("Unhandled error: %s", err)
        err = HttpsError(FunctionsErrorCode.INTERNAL, "INTERNAL")

    return {"error": err._as_dict()}, err._http_error_code.status


def _add_cors_headers_to_response(
    response,  # Can be Flask Response or Starlette Response
    cors_options: CorsOptions | None,
    allowed_methods: list[str] | None = None,
) -> None:
    """Add CORS headers to any response object with headers dict."""
    if not cors_options:
        return

    origins = cors_options.cors_origins or "*"
    if isinstance(origins, list):
        origins = ", ".join(origins)

    methods = allowed_methods or cors_options.cors_methods or ["*"]
    if isinstance(methods, list):
        methods = ", ".join(methods)

    response.headers["Access-Control-Allow-Origin"] = origins
    response.headers["Access-Control-Allow-Methods"] = methods
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, Firebase-Instance-ID-Token, "
        "Firebase-AppCheck, X-Firebase-AppCheck"
    )

    if origins != "*":
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"


def _on_call_handler(func: _C2, request: Request, enforce_app_check: bool) -> Response:
    """Sync on_call handler using shared logic."""
    try:
        # Use shared processing
        context = _process_on_call_request_body(
            raw_request=request,
            body_bytes=request.data,
            headers=dict(request.headers),
            method=request.method,
            enforce_app_check=enforce_app_check,
        )

        # Call function
        result = _core._with_init(func)(context)

        # Format response
        return _jsonify(_format_on_call_response(result))

    # Disable broad exceptions lint since we want to handle all exceptions here
    # and wrap as an HttpsError.
    # pylint: disable=broad-except
    except Exception as err:
        error_dict, status = _format_on_call_error(err)
        return _make_response(_jsonify(error_dict), status)


async def _on_call_handler_async(func: _C2, request, enforce_app_check: bool):
    """Async on_call handler using shared logic."""
    # Import here to avoid runtime dependency when not using async
    from starlette.responses import JSONResponse

    try:
        # Read body (only async-specific part)
        body_bytes = await request.body()

        # Use shared processing
        context = _process_on_call_request_body(
            raw_request=request,
            body_bytes=body_bytes,
            headers=dict(request.headers),
            method=request.method,
            enforce_app_check=enforce_app_check,
        )

        # Call function (check if it's async or sync)
        if _inspect.iscoroutinefunction(func):
            result = await _core._with_init(func)(context)
        else:
            result = _core._with_init(func)(context)

        # Format response
        return JSONResponse(_format_on_call_response(result))

    # Disable broad exceptions lint since we want to handle all exceptions here
    # and wrap as an HttpsError.
    # pylint: disable=broad-except
    except Exception as err:
        error_dict, status = _format_on_call_error(err)
        return JSONResponse(content=error_dict, status_code=status)


@_typing.overload
def _create_on_request_decorator(func: _C1, options: HttpsOptions, asgi: _typing.Literal[False] = False) -> _C1:
    ...

@_typing.overload
def _create_on_request_decorator(func: _typing.Callable[..., _typing.Awaitable[_typing.Any]], options: HttpsOptions, asgi: _typing.Literal[True]) -> _typing.Callable[..., _typing.Awaitable[_typing.Any]]:
    ...

def _create_on_request_decorator(func: _typing.Union[_C1, _typing.Callable[..., _typing.Awaitable[_typing.Any]]], options: HttpsOptions, asgi: bool = False) -> _typing.Union[_C1, _typing.Callable[..., _typing.Awaitable[_typing.Any]]]:
    """
    Internal helper to create the on_request decorator wrapper.
    This shared implementation is used by both sync and async versions.
    """
    if asgi:
        # For async functions, we need an async wrapper
        @_functools.wraps(func)
        async def async_wrapper(request):  # Will receive Starlette Request
            # Import here to avoid runtime dependency when not using async
            from starlette.responses import JSONResponse
            from starlette.responses import Response as StarletteResponse

            # Handle OPTIONS preflight
            if request.method == "OPTIONS" and options.cors:
                response = StarletteResponse(status_code=200)
                _add_cors_headers_to_response(response, options.cors)
                return response

            # Call the function (check if it's async or sync)
            if _inspect.iscoroutinefunction(func):
                result = await _core._with_init(func)(request)
            else:
                result = _core._with_init(func)(request)

            # Convert to response
            if isinstance(result, dict):
                response = JSONResponse(result)
            elif hasattr(result, "headers"):  # Already a response
                response = result
            else:
                response = StarletteResponse(content=str(result))

            # Add CORS headers
            _add_cors_headers_to_response(response, options.cors)
            return response

        wrapper = async_wrapper
    else:
        # For sync functions, use the existing logic
        @_functools.wraps(func)
        def sync_wrapper(request: Request) -> Response:
            if options.cors is not None:
                return _cross_origin(
                    methods=options.cors.cors_methods,
                    origins=options.cors.cors_origins,
                )(func)(request)
            return _core._with_init(func)(request)

        wrapper = sync_wrapper

    _util.set_func_endpoint_attr(
        wrapper,
        options._endpoint(func_name=func.__name__, asgi=asgi),
    )
    return _typing.cast(_C1, wrapper)


@_util.copy_func_kwargs(HttpsOptions)
def on_request(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Handler which handles HTTPS requests.
    Requires a function that takes a ``Request`` and ``Response`` object,
    the same signature as a Flask app.

    Example:

    .. code-block:: python

      @on_request()
      def example(request: Request) -> Response:
          pass

    :param \\*\\*kwargs: Https options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.HttpsOptions`
    :rtype: :exc:`typing.Callable` \\[ \\[ :exc:`flask.Request` \\], :exc:`flask.Response` \\]
            A function that takes a :exc:`flask.Request` and returns a :exc:`flask.Response`.
    """
    options = HttpsOptions(**kwargs)

    def on_request_inner_decorator(func: _C1):
        return _create_on_request_decorator(func, options, asgi=False)

    return on_request_inner_decorator


@_typing.overload
def _create_on_call_decorator(func: _C2, options: HttpsOptions, asgi: _typing.Literal[False] = False) -> _C2:
    ...

@_typing.overload
def _create_on_call_decorator(func: _typing.Callable[..., _typing.Awaitable[_typing.Any]], options: HttpsOptions, asgi: _typing.Literal[True]) -> _typing.Callable[..., _typing.Awaitable[_typing.Any]]:
    ...

def _create_on_call_decorator(func: _typing.Union[_C2, _typing.Callable[..., _typing.Awaitable[_typing.Any]]], options: HttpsOptions, asgi: bool = False) -> _typing.Union[_C2, _typing.Callable[..., _typing.Awaitable[_typing.Any]]]:
    """
    Internal helper to create the on_call decorator wrapper.
    This shared implementation is used by both sync and async versions.
    """
    origins: _typing.Any = "*"
    if options.cors is not None and options.cors.cors_origins is not None:
        origins = options.cors.cors_origins

    # Default to False.
    enforce_app_check = False
    # If the global option is set, use that.
    if options.enforce_app_check is None and _GLOBAL_OPTIONS.enforce_app_check is not None:
        enforce_app_check = _GLOBAL_OPTIONS.enforce_app_check
    # If the global option is not set, use the local option.
    elif options.enforce_app_check is not None:
        enforce_app_check = options.enforce_app_check

    if asgi:
        # For async callable functions
        @_functools.wraps(func)
        async def async_wrapper(request):  # Will receive Starlette Request
            # Import here to avoid runtime dependency when not using async
            from starlette.responses import Response as StarletteResponse

            # Handle OPTIONS preflight
            if request.method == "OPTIONS" and options.cors:
                response = StarletteResponse(status_code=200)
                _add_cors_headers_to_response(response, options.cors, ["POST"])
                return response

            # Use async handler
            response = await _on_call_handler_async(func, request, enforce_app_check)

            # Add CORS headers
            _add_cors_headers_to_response(response, options.cors, ["POST"])
            return response

        wrapper = async_wrapper
    else:
        # For sync callable functions
        @_cross_origin(
            methods="POST",
            origins=origins,
        )
        @_functools.wraps(func)
        def sync_wrapper(request: Request):
            return _on_call_handler(
                func,
                request,
                enforce_app_check,
            )

        wrapper = sync_wrapper

    _util.set_func_endpoint_attr(
        wrapper,
        options._endpoint(func_name=func.__name__, callable=True, asgi=asgi),
    )
    return _typing.cast(_C2, wrapper)


@_util.copy_func_kwargs(HttpsOptions)
def on_call(**kwargs) -> _typing.Callable[[_C2], _C2]:
    """
    Declares a callable method for clients to call using a Firebase SDK.
    Requires a function that takes a ``CallableRequest``.

    Example:

    .. code-block:: python

      @on_call()
      def example(request: CallableRequest) -> Any:
          return "Hello World"

    :param \\*\\*kwargs: Https options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.HttpsOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.https.CallableRequest` \\[
            :exc:`object` \\] \\], :exc:`object` \\]
            A function that takes a ``CallableRequest`` and returns an :exc:`object`.
    """
    options = HttpsOptions(**kwargs)

    def on_call_inner_decorator(func: _C2):
        return _create_on_call_decorator(func, options, asgi=False)

    return on_call_inner_decorator
