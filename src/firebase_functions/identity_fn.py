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
"""Cloud functions to handle Eventarc events."""

# pylint: disable=protected-access
import typing as _typing
import functools as _functools
import datetime as _dt
import time as _time
import json as _json
import dataclasses as _dataclasses
from firebase_functions.https_fn import HttpsError, FunctionsErrorCode

import firebase_functions.options as _options
import firebase_functions.private.util as _util
import firebase_functions.private.token_verifier as _token_verifier
from flask import (
    Request as _Request,
    Response as _Response,
    make_response as _make_response,
    jsonify as _jsonify,
)
from functions_framework import logging as _logging


@_dataclasses.dataclass(frozen=True)
class AuthUserInfo:
    """
    User info that is part of the AuthUserRecord.
    """
    uid: str
    """The user identifier for the linked provider."""

    provider_id: str
    """The linked provider ID (e.g., "google.com" for the Google provider)."""

    display_name: str | None = None
    """The display name for the linked provider."""

    email: str | None = None
    """The email for the linked provider."""

    photo_url: str | None = None
    """The photo URL for the linked provider."""

    phone_number: str | None = None
    """The phone number for the linked provider."""

    @classmethod
    def from_json(cls, json_data: dict[str, _typing.Any]) -> "AuthUserInfo":
        return cls(
            uid=json_data["uid"],
            provider_id=json_data["provider_id"],
            display_name=json_data.get("display_name"),
            email=json_data.get("email"),
            photo_url=json_data.get("photo_url"),
            phone_number=json_data.get("phone_number"),
        )


@_dataclasses.dataclass(frozen=True)
class AuthUserMetadata:
    """
    Additional metadata about the user.
    """
    creation_time: _dt.datetime
    """The date the user was created."""

    last_sign_in_time: _dt.datetime
    """The date the user last signed in."""

    @classmethod
    def from_json(cls, json_data: dict[str, _typing.Any]) -> "AuthUserMetadata":
        return cls(
            creation_time=_dt.datetime.utcfromtimestamp(
                json_data["creation_time"] / 1000.0),
            last_sign_in_time=_dt.datetime.utcfromtimestamp(
                json_data["last_sign_in_time"] / 1000.0),
        )


@_dataclasses.dataclass(frozen=True)
class AuthMultiFactorInfo:
    """
    Interface representing the common properties of a user-enrolled second factor.
    """

    uid: str
    """
    The ID of the enrolled second factor. This ID is unique to the user.
    """

    display_name: str | None
    """
    The optional display name of the enrolled second factor.
    """

    factor_id: str
    """
    The type identifier of the second factor. For SMS second factors, this is `phone`.
    """

    enrollment_time: _dt.datetime | None
    """
    The optional date the second factor was enrolled.
    """

    phone_number: str | None
    """
    The phone number associated with a phone second factor.
    """

    @classmethod
    def from_json(cls, json_data: dict[str,
                                       _typing.Any]) -> "AuthMultiFactorInfo":
        enrollment_time = json_data.get("enrollment_time")
        if enrollment_time:
            enrollment_time = _dt.datetime.fromisoformat(enrollment_time)

        factor_id = json_data["factor_id"] if not json_data.get(
            "phone_number") else "phone"

        return cls(
            uid=json_data["uid"],
            factor_id=factor_id,
            display_name=json_data.get("display_name"),
            enrollment_time=enrollment_time,
            phone_number=json_data.get("phone_number"),
        )


@_dataclasses.dataclass(frozen=True)
class AuthMultiFactorSettings:
    """
    The multi-factor related properties for the current user, if available.
    """

    enrolled_factors: list[AuthMultiFactorInfo]
    """
    List of second factors enrolled with the current user.
    """

    @classmethod
    def from_json(cls, json_data: dict[str, _typing.Any]):
        if not json_data:
            return None

        enrolled_factors = [
            AuthMultiFactorInfo.from_json(factor)
            for factor in json_data.get("enrolled_factors", [])
        ]

        if not enrolled_factors:
            return None

        return cls(enrolled_factors=enrolled_factors)


@_dataclasses.dataclass(frozen=True)
class AuthUserRecord:
    """
    The UserRecord passed to auth blocking Cloud Functions from the identity platform.
    """

    uid: str
    """
    The user's `uid`.
    """

    email: str | None
    """
    The user's primary email, if set.
    """

    email_verified: bool
    """
    Whether or not the user's primary email is verified.
    """

    display_name: str | None
    """
    The user's display name.
    """

    photo_url: str | None
    """
    The user's photo URL.
    """

    phone_number: str | None
    """
    The user's primary phone number, if set.
    """

    disabled: bool
    """
    Whether or not the user is disabled: `true` for disabled; `false` for enabled.
    """

    metadata: AuthUserMetadata
    """
    Additional metadata about the user.
    """

    provider_data: list[AuthUserInfo]
    """
    An array of providers (e.g., Google, Facebook) linked to the user.
    """

    password_hash: str | None
    """
    The user's hashed password (base64-encoded).
    """

    password_salt: str | None
    """
    The user's password salt (base64-encoded).
    """

    custom_claims: dict[str, _typing.Any] | None
    """
    The user's custom claims object if available.
    """

    tenant_id: str | None
    """
    The ID of the tenant the user belongs to, if available.
    """

    tokens_valid_after_time: _dt.datetime | None
    """The date the user's tokens are valid after."""

    multi_factor: AuthMultiFactorSettings | None
    """The multi-factor related properties for the current user, if available."""

    @classmethod
    def from_json(cls, json_data: dict[str, _typing.Any]) -> "AuthUserRecord":
        return cls(
            uid=json_data["uid"],
            email=json_data.get("email"),
            email_verified=json_data["email_verified"],
            display_name=json_data.get("display_name"),
            photo_url=json_data.get("photo_url"),
            phone_number=json_data.get("phone_number"),
            disabled=json_data.get("disabled", False),
            metadata=AuthUserMetadata.from_json(json_data["metadata"]),
            provider_data=[
                AuthUserInfo.from_json(info)
                for info in json_data["provider_data"]
            ],
            password_hash=json_data.get("password_hash"),
            password_salt=json_data.get("password_salt"),
            custom_claims=json_data.get("custom_claims"),
            tenant_id=json_data.get("tenant_id"),
            tokens_valid_after_time=_dt.datetime.utcfromtimestamp(
                json_data["tokens_valid_after_time"])
            if json_data.get("tokens_valid_after_time") else None,
            multi_factor=AuthMultiFactorSettings.from_json(
                json_data["multi_factor"])
            if "multi_factor" in json_data else None,
        )


@_dataclasses.dataclass(frozen=True)
class AdditionalUserInfo:
    """
    The additional user info component of the auth event context.
    """

    provider_id: str
    """The provider identifier."""

    profile: dict[str, _typing.Any] | None
    """The user's profile data as a dictionary."""

    username: str | None
    """The user's username, if available."""

    is_new_user: bool
    """A boolean indicating if the user is new or not."""

    @classmethod
    def from_json(cls, json_data: dict[str,
                                       _typing.Any]) -> "AdditionalUserInfo":
        raw_user_info = json_data.get("raw_user_info")
        profile = None
        username = None
        if raw_user_info:
            try:
                profile = _json.loads(raw_user_info)
            except _json.JSONDecodeError as err:
                _logging.debug(f"Parse Error: {err.msg}")
        if profile:
            sign_in_method = json_data.get("sign_in_method")
            if sign_in_method == "github.com":
                username = profile.get("login")
            elif sign_in_method == "twitter.com":
                username = profile.get("screen_name")

        provider_id: str = ("password" if json_data.get("sign_in_method")
                            == "emailLink" else str(
                                json_data.get("sign_in_method")))

        is_new_user = json_data.get("event_type") == "beforeCreate"

        return cls(
            provider_id=provider_id,
            profile=profile,
            username=username,
            is_new_user=is_new_user,
        )


@_dataclasses.dataclass(frozen=True)
class Credential:
    """
    The credential component of the auth event context.
    """

    claims: dict[str, _typing.Any] | None
    """The user's claims data as a dictionary."""

    id_token: str | None
    """The user's ID token."""

    access_token: str | None
    """The user's access token."""

    refresh_token: str | None
    """The user's refresh token."""

    expiration_time: _dt.datetime | None
    """The expiration time of the user's access token."""

    secret: str | None
    """The user's secret."""

    provider_id: str
    """The provider identifier."""

    sign_in_method: str
    """The user's sign-in method."""

    @classmethod
    def from_json(cls, json_data: dict[str, _typing.Any], time: float):
        if (not json_data.get("sign_in_attributes") and
                not json_data.get("oauth_id_token") and
                not json_data.get("oauth_access_token") and
                not json_data.get("oauth_refresh_token")):
            return None

        oauth_expires_in = json_data.get("oauth_expires_in")
        expiration_time = (_dt.datetime.utcfromtimestamp(time +
                                                         oauth_expires_in)
                           if oauth_expires_in else None)

        provider_id: str = ("password" if json_data.get("sign_in_method")
                            == "emailLink" else str(
                                json_data.get("sign_in_method")))

        return cls(
            claims=json_data.get("sign_in_attributes"),
            id_token=json_data.get("oauth_id_token"),
            access_token=json_data.get("oauth_access_token"),
            refresh_token=json_data.get("oauth_refresh_token"),
            expiration_time=expiration_time,
            secret=json_data.get("oauth_token_secret"),
            provider_id=provider_id,
            sign_in_method=json_data["sign_in_method"],
        )


@_dataclasses.dataclass(frozen=True)
class BeforeCreateResponse:
    """
    The handler response type for 'beforeCreate' blocking events.
    """

    display_name: str | None = None
    """The user's display name."""

    disabled: bool | None = None
    """Whether or not the user is disabled."""

    email_verified: bool | None = None
    """Whether or not the user's primary email is verified."""

    photo_url: str | None = None
    """The user's photo URL."""

    custom_claims: dict[str, _typing.Any] | None = None
    """The user's custom claims object if available."""


@_dataclasses.dataclass(frozen=True)
class BeforeSignInResponse(BeforeCreateResponse):
    """
    The handler response type for 'beforeSignIn' blocking events.
    """

    session_claims: dict[str, _typing.Any] | None = None
    """The user's session claims object if available."""


@_dataclasses.dataclass(frozen=True)
class AuthBlockingEvent:
    """
    Defines an auth event for identitytoolkit v2 auth blocking events.
    """

    data: AuthUserRecord
    """
    The UserRecord passed to auth blocking Cloud Functions from the identity platform.
    """

    locale: str | None
    """
    The application locale. You can set the locale using the client SDK, 
    or by passing the locale header in the REST API.
    Example: 'fr' or 'sv-SE'
    """

    event_id: str
    """
    The event's unique identifier.
    Example: 'rWsyPtolplG2TBFoOkkgyg'
    """

    ip_address: str
    """
    The IP address of the device the end user is registering or signing in from.
    Example: '114.14.200.1'
    """

    user_agent: str
    """
    The user agent triggering the blocking function.
    Example: 'Mozilla/5.0 (X11; Linux x86_64)'
    """

    additional_user_info: AdditionalUserInfo
    """An object containing information about the user."""

    credential: Credential | None
    """An object containing information about the user's credential."""

    timestamp: _dt.datetime
    """
    The time the event was triggered."""

    @classmethod
    def from_json(cls, json_data: dict[str,
                                       _typing.Any]) -> "AuthBlockingEvent":
        return cls(
            data=AuthUserRecord.from_json(json_data["user_record"]),
            locale=json_data.get("locale"),
            event_id=json_data["event_id"],
            ip_address=json_data["ip_address"],
            user_agent=json_data["user_agent"],
            timestamp=_dt.datetime.fromtimestamp(json_data["iat"]),
            additional_user_info=AdditionalUserInfo.from_json(json_data),
            credential=Credential.from_json(json_data, _time.time()),
        )


_C1 = _typing.Callable[[AuthBlockingEvent], BeforeCreateResponse | None]
_C2 = _typing.Callable[[AuthBlockingEvent], BeforeSignInResponse | None]
_event_type_before_create = "providers/cloud.auth/eventTypes/user.beforeCreate"
_event_type_before_sign_in = "providers/cloud.auth/eventTypes/user.beforeSignIn"
_claims_max_payload_size = 1000
_disallowed_custom_claims = [
    "acr",
    "amr",
    "at_hash",
    "aud",
    "auth_time",
    "azp",
    "cnf",
    "c_hash",
    "exp",
    "iat",
    "iss",
    "jti",
    "nbf",
    "nonce",
    "firebase",
]


def _validate_auth_response(
    event_type: str,
    auth_request: BeforeCreateResponse | BeforeSignInResponse | None = None,
):
    if auth_request is None:
        auth_request = BeforeCreateResponse()

    if auth_request.custom_claims:
        invalid_claims = [
            claim for claim in _disallowed_custom_claims
            if claim in auth_request.custom_claims
        ]

        if invalid_claims:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f'The custom_claims claims "{",".join(invalid_claims)}" are reserved '
                f"and cannot be specified.")

        if len(_json.dumps(
                auth_request.custom_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The custom_claims payload should not exceed "
                f"{_claims_max_payload_size} characters.")

    if event_type == _event_type_before_sign_in and isinstance(
            auth_request, BeforeSignInResponse) and auth_request.session_claims:

        invalid_claims = [
            claim for claim in _disallowed_custom_claims
            if claim in auth_request.session_claims
        ]

        if invalid_claims:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f'The session_claims claims "{",".join(invalid_claims)}" are reserved '
                f"and cannot be specified.",
            )

        if len(_json.dumps(
                auth_request.session_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The session_claims payload should not exceed "
                f"{_claims_max_payload_size} characters.",
            )

        combined_claims = {
            **(auth_request.custom_claims if auth_request.custom_claims else {}),
            **auth_request.session_claims
        }

        if len(_json.dumps(combined_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The customClaims and session_claims payloads should not exceed "
                f"{_claims_max_payload_size} characters combined.")


def _before_operation_handler(
    func: _C1 | _C2,
    event_type: str,
    request: _Request,
) -> _Response:
    try:
        if not _util.valid_on_call_request(request):
            _logging.error("Invalid request, unable to process.")
            raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")
        if request.json is None:
            _logging.error("Request is missing body.")
            raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")
        if request.json is None or "data" not in request.json:
            _logging.error("Request body is missing data.", request.json)
            raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad Request")
        jwt_token = request.json["data"]["jwt"]
        decoded_token = _token_verifier.verify_auth_blocking_token(jwt_token)
        event = AuthBlockingEvent.from_json(decoded_token)
        auth_response: BeforeCreateResponse | BeforeSignInResponse | None = func(
            event)
        if not auth_response:
            return _jsonify(result={})

        _validate_auth_response(event_type, auth_response)

        # TODO: photoURL vs photoUrl, we want to use photoURL
        # TODO: updateMask is showing all fields instead of just the ones that were updated
        auth_response_dict = _util.convert_keys_to_camel_case(
            _dataclasses.asdict(auth_response))
        update_mask = ",".join(auth_response_dict.keys())
        # TODO: remove this after testing
        print(auth_response_dict)
        print(update_mask)
        return _jsonify(result={
            "userRecord": {
                **auth_response_dict,
                "updateMask": update_mask,
            }
        })
    # Disable broad exceptions lint since we want to handle all exceptions.
    # pylint: disable=broad-except
    except Exception as exception:
        if not isinstance(exception, HttpsError):
            _logging.error("Unhandled error", exception)
            exception = HttpsError(FunctionsErrorCode.INTERNAL, "INTERNAL")
        status = exception._http_error_code.status
        return _make_response(_jsonify(error=exception._as_dict()), status)


@_util.copy_func_kwargs(_options.BlockingOptions)
def before_user_signed_in(**kwargs,) -> _typing.Callable[[_C2], _C2]:
    """
    Handles an event that is triggered before a user is signed in.

    Example:

    .. code-block:: python

      from firebase_functions import identity_fn

      @identity_fn.before_user_signed_in()
      def example(event: identity_fn.AuthBlockingEvent) -> identity_fn.BeforeSignInResponse | None:
          pass

    :param \\*\\*kwargs: Options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.BlockingOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.identity_fn.AuthBlockingEvent` \\], 
            :exc:`firebase_functions.identity_fn.BeforeSignInResponse` \\| `None` \\]
            A function that takes a AuthBlockingEvent and optionally returns BeforeSignInResponse.
    """
    options = _options.BlockingOptions(**kwargs)

    def before_user_signed_in_decorator(func: _C2):

        @_functools.wraps(func)
        def before_user_signed_in_wrapped(request: _Request) -> _Response:
            return _before_operation_handler(
                func,
                _event_type_before_sign_in,
                request,
            )

        _util.set_func_endpoint_attr(
            before_user_signed_in_wrapped,
            options._endpoint(
                func_name=func.__name__,
                event_type=_event_type_before_sign_in,
            ),
        )
        _util.set_required_apis_attr(
            before_user_signed_in_wrapped,
            options._required_apis(),
        )
        return before_user_signed_in_wrapped

    return before_user_signed_in_decorator


@_util.copy_func_kwargs(_options.BlockingOptions)
def before_user_created(**kwargs,) -> _typing.Callable[[_C1], _C1]:
    """
    Handles an event that is triggered before a user is created.

    Example:

    .. code-block:: python

      from firebase_functions import identity_fn

      @identity_fn.before_user_created()
      def example(event: identity_fn.AuthBlockingEvent) -> identity_fn.BeforeCreateResponse | None:
          pass

    :param \\*\\*kwargs: Options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.BlockingOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.identity_fn.AuthBlockingEvent` \\], 
            :exc:`firebase_functions.identity_fn.BeforeCreateResponse` \\| `None` \\]
            A function that takes a AuthBlockingEvent and optionally returns BeforeCreateResponse.
    """
    options = _options.BlockingOptions(**kwargs)

    def before_user_created_decorator(func: _C1):

        @_functools.wraps(func)
        def before_user_created_wrapped(request: _Request) -> _Response:
            return _before_operation_handler(
                func,
                _event_type_before_create,
                request,
            )

        _util.set_func_endpoint_attr(
            before_user_created_wrapped,
            options._endpoint(
                func_name=func.__name__,
                event_type=_event_type_before_create,
            ),
        )
        _util.set_required_apis_attr(
            before_user_created_wrapped,
            options._required_apis(),
        )
        return before_user_created_wrapped

    return before_user_created_decorator
