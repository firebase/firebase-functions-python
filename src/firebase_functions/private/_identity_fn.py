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
import datetime as _dt
import json as _json
import time as _time
import typing as _typing

from flask import (
    Request as _Request,
)
from flask import (
    Response as _Response,
)
from flask import (
    jsonify as _jsonify,
)
from flask import (
    make_response as _make_response,
)
from functions_framework import logging as _logging

import firebase_functions.private.token_verifier as _token_verifier
import firebase_functions.private.util as _util
from firebase_functions.core import _with_init
from firebase_functions.https_fn import FunctionsErrorCode, HttpsError

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


def _auth_user_info_from_token_data(token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AuthUserInfo

    return AuthUserInfo(
        uid=token_data["uid"],
        provider_id=token_data["provider_id"],
        display_name=token_data.get("display_name"),
        email=token_data.get("email"),
        photo_url=token_data.get("photo_url"),
        phone_number=token_data.get("phone_number"),
    )


def _auth_user_metadata_from_token_data(token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AuthUserMetadata

    creation_time = _dt.datetime.utcfromtimestamp(int(token_data["creation_time"]) / 1000.0)
    last_sign_in_time = None
    if "last_sign_in_time" in token_data:
        last_sign_in_time = _dt.datetime.utcfromtimestamp(
            int(token_data["last_sign_in_time"]) / 1000.0
        )

    return AuthUserMetadata(creation_time=creation_time, last_sign_in_time=last_sign_in_time)


def _auth_multi_factor_info_from_token_data(token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AuthMultiFactorInfo

    enrollment_time = token_data.get("enrollment_time")
    if enrollment_time:
        enrollment_time = _dt.datetime.fromisoformat(enrollment_time)
    factor_id = token_data["factor_id"] if not token_data.get("phone_number") else "phone"
    return AuthMultiFactorInfo(
        uid=token_data["uid"],
        factor_id=factor_id,
        display_name=token_data.get("display_name"),
        enrollment_time=enrollment_time,
        phone_number=token_data.get("phone_number"),
    )


def _auth_multi_factor_settings_from_token_data(token_data: dict[str, _typing.Any]):
    if not token_data:
        return None

    from firebase_functions.identity_fn import AuthMultiFactorSettings

    enrolled_factors = [
        _auth_multi_factor_info_from_token_data(factor)
        for factor in token_data.get("enrolled_factors", [])
    ]

    if not enrolled_factors:
        return None

    return AuthMultiFactorSettings(enrolled_factors=enrolled_factors)


def _auth_user_record_from_token_data(token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AuthUserRecord

    return AuthUserRecord(
        uid=token_data["uid"],
        email=token_data.get("email"),
        email_verified=bool(token_data.get("email_verified")),
        display_name=token_data.get("display_name"),
        photo_url=token_data.get("photo_url"),
        phone_number=token_data.get("phone_number"),
        disabled=token_data.get("disabled", False),
        metadata=_auth_user_metadata_from_token_data(token_data["metadata"]),
        provider_data=[
            _auth_user_info_from_token_data(info) for info in token_data["provider_data"]
        ],
        password_hash=token_data.get("password_hash"),
        password_salt=token_data.get("password_salt"),
        custom_claims=token_data.get("custom_claims"),
        tenant_id=token_data.get("tenant_id"),
        tokens_valid_after_time=_dt.datetime.utcfromtimestamp(token_data["tokens_valid_after_time"])
        if token_data.get("tokens_valid_after_time")
        else None,
        multi_factor=_auth_multi_factor_settings_from_token_data(token_data["multi_factor"])
        if "multi_factor" in token_data
        else None,
    )


def _additional_user_info_from_token_data(token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AdditionalUserInfo

    raw_user_info = token_data.get("raw_user_info")
    profile = None
    username = None
    if raw_user_info:
        try:
            profile = _json.loads(raw_user_info)
        except _json.JSONDecodeError as err:
            _logging.debug(f"Parse Error: {err.msg}")
    if profile:
        sign_in_method = token_data.get("sign_in_method")
        if sign_in_method == "github.com":
            username = profile.get("login")
        elif sign_in_method == "twitter.com":
            username = profile.get("screen_name")

    provider_id: str = (
        "password"
        if token_data.get("sign_in_method") == "emailLink"
        else str(token_data.get("sign_in_method"))
    )

    is_new_user = token_data.get("event_type") == "beforeCreate"

    return AdditionalUserInfo(
        provider_id=provider_id,
        profile=profile,
        username=username,
        is_new_user=is_new_user,
        recaptcha_score=token_data.get("recaptcha_score"),
    )


def _credential_from_token_data(token_data: dict[str, _typing.Any], time: float):
    if (
        not token_data.get("sign_in_attributes")
        and not token_data.get("oauth_id_token")
        and not token_data.get("oauth_access_token")
        and not token_data.get("oauth_refresh_token")
    ):
        return None

    from firebase_functions.identity_fn import Credential

    oauth_expires_in = token_data.get("oauth_expires_in")
    expiration_time = (
        _dt.datetime.utcfromtimestamp(time + oauth_expires_in) if oauth_expires_in else None
    )

    provider_id: str = (
        "password"
        if token_data.get("sign_in_method") == "emailLink"
        else str(token_data.get("sign_in_method"))
    )

    return Credential(
        claims=token_data.get("sign_in_attributes"),
        id_token=token_data.get("oauth_id_token"),
        access_token=token_data.get("oauth_access_token"),
        refresh_token=token_data.get("oauth_refresh_token"),
        expiration_time=expiration_time,
        secret=token_data.get("oauth_token_secret"),
        provider_id=provider_id,
        sign_in_method=token_data["sign_in_method"],
    )


def _auth_blocking_event_from_token_data(event_type: str, token_data: dict[str, _typing.Any]):
    from firebase_functions.identity_fn import AuthBlockingEvent

    return AuthBlockingEvent(
        data=_auth_user_record_from_token_data(token_data["user_record"]),
        locale=token_data.get("locale"),
        event_type=event_type,
        event_id=token_data["event_id"],
        ip_address=token_data["ip_address"],
        user_agent=token_data["user_agent"],
        timestamp=_dt.datetime.fromtimestamp(token_data["iat"]),
        additional_user_info=_additional_user_info_from_token_data(token_data),
        credential=_credential_from_token_data(token_data, _time.time()),
        email_type=token_data.get("email_type"),
        sms_type=token_data.get("sms_type"),
    )


event_type_before_create = "providers/cloud.auth/eventTypes/user.beforeCreate"
event_type_before_sign_in = "providers/cloud.auth/eventTypes/user.beforeSignIn"


def _validate_auth_response(
    event_type: str,
    auth_response,
) -> dict[str, _typing.Any]:
    if auth_response is None:
        auth_response = {}

    custom_claims: dict[str, _typing.Any] | None = auth_response.get("custom_claims")
    session_claims: dict[str, _typing.Any] | None = auth_response.get("session_claims")

    if session_claims and event_type == event_type_before_create:
        raise HttpsError(
            FunctionsErrorCode.INVALID_ARGUMENT,
            f'The session_claims claims "{",".join(session_claims)}" cannot be specified '
            f"for the before_create event.",
        )

    if custom_claims:
        invalid_claims = [claim for claim in _disallowed_custom_claims if claim in custom_claims]

        if invalid_claims:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f'The custom_claims claims "{",".join(invalid_claims)}" are reserved '
                f"and cannot be specified.",
            )

        if len(_json.dumps(custom_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The custom_claims payload should not exceed "
                f"{_claims_max_payload_size} characters.",
            )

    if event_type == event_type_before_sign_in and session_claims:
        invalid_claims = [claim for claim in _disallowed_custom_claims if claim in session_claims]

        if invalid_claims:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f'The session_claims claims "{",".join(invalid_claims)}" are reserved '
                f"and cannot be specified.",
            )

        if len(_json.dumps(session_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The session_claims payload should not exceed "
                f"{_claims_max_payload_size} characters.",
            )

        combined_claims = {**(custom_claims if custom_claims else {}), **session_claims}

        if len(_json.dumps(combined_claims)) > _claims_max_payload_size:
            raise HttpsError(
                FunctionsErrorCode.INVALID_ARGUMENT,
                f"The customClaims and session_claims payloads should not exceed "
                f"{_claims_max_payload_size} characters combined.",
            )

    auth_response_dict = {}
    auth_response_keys = set(auth_response.keys())
    if "display_name" in auth_response_keys:
        auth_response_dict["displayName"] = auth_response["display_name"]
    if "disabled" in auth_response_keys:
        auth_response_dict["disabled"] = auth_response["disabled"]
    if "email_verified" in auth_response_keys:
        auth_response_dict["emailVerified"] = auth_response["email_verified"]
    if "photo_url" in auth_response_keys:
        auth_response_dict["photoURL"] = auth_response["photo_url"]
    if "custom_claims" in auth_response_keys:
        auth_response_dict["customClaims"] = auth_response["custom_claims"]
    if "session_claims" in auth_response_keys:
        auth_response_dict["sessionClaims"] = auth_response["session_claims"]
    if "recaptcha_action_override" in auth_response_keys:
        auth_response_dict["recaptchaActionOverride"] = auth_response["recaptcha_action_override"]
    return auth_response_dict


def _generate_response_payload(
    auth_response_dict: dict[str, _typing.Any] | None,
) -> dict[str, _typing.Any]:
    if not auth_response_dict:
        return {}

    formatted_auth_response = auth_response_dict.copy()
    recaptcha_action_override = formatted_auth_response.pop("recaptchaActionOverride", None)
    result = {}
    update_mask = ",".join(formatted_auth_response.keys())

    if len(update_mask) != 0:
        result["userRecord"] = {**formatted_auth_response, "updateMask": update_mask}

    if recaptcha_action_override is not None:
        result["recaptchaActionOverride"] = recaptcha_action_override

    return result


def before_operation_handler(
    func: _typing.Callable,
    event_type: str,
    request: _Request,
) -> _Response:
    from firebase_functions.identity_fn import BeforeCreateResponse, BeforeSignInResponse

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
        event = _auth_blocking_event_from_token_data(event_type, decoded_token)
        auth_response: BeforeCreateResponse | BeforeSignInResponse | None = _with_init(func)(event)
        if not auth_response:
            return _jsonify({})
        auth_response_dict = _validate_auth_response(event_type, auth_response)
        result = _generate_response_payload(auth_response_dict)
        return _jsonify(result)
    # Disable broad exceptions lint since we want to handle all exceptions.
    # pylint: disable=broad-except
    except Exception as exception:
        if not isinstance(exception, HttpsError):
            _logging.error("Unhandled error %s", exception)
            exception = HttpsError(FunctionsErrorCode.INTERNAL, "INTERNAL")
        status = exception._http_error_code.status
        return _make_response(_jsonify(error=exception._as_dict()), status)
