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
"""
Module for internal token verification.
"""

import google.auth.exceptions
import google.oauth2.id_token
import google.oauth2.service_account
from firebase_admin import (
    _DEFAULT_APP_NAME,
    _apps,
    _auth_utils,
    _token_gen,
    exceptions,
    get_app,
    initialize_app,
)
from google.auth import jwt


# pylint: disable=consider-using-f-string
# mypy: ignore-errors
# TODO remove once firebase-admin supports this directly.
# Modified from src/firebase_admin/_token_gen.py to add
# support for app_check tokens (expected_audience kwarg and
# usage are new, plus None for audience on google.oauth2.id_token.verify_token call)
class _JWTVerifier:
    """Verifies Firebase JWTs (ID tokens or session cookies)."""

    def __init__(self, **kwargs):
        self.project_id = kwargs.pop("project_id")
        self.short_name = kwargs.pop("short_name")
        self.operation = kwargs.pop("operation")
        self.url = kwargs.pop("doc_url")
        self.cert_url = kwargs.pop("cert_url")
        self.issuer = kwargs.pop("issuer")
        self.expected_audience = kwargs.pop("expected_audience")
        if self.short_name[0].lower() in "aeiou":
            self.articled_short_name = f"an {self.short_name}"
        else:
            self.articled_short_name = f"a {self.short_name}"
        self._invalid_token_error = kwargs.pop("invalid_token_error")
        self._expired_token_error = kwargs.pop("expired_token_error")

    def verify(self, token, request):
        """Verifies the signature and data for the provided JWT."""
        token = token.encode("utf-8") if isinstance(token, str) else token
        if not isinstance(token, bytes) or not token:
            raise ValueError(
                f"Illegal {self.short_name} provided: {token}. {self.short_name} must be a non-empty string."
            )

        if not self.project_id:
            raise ValueError(
                "Failed to ascertain project ID from the credential or the environment. Project "
                f"ID is required to call {self.operation}. Initialize the app with a credentials.Certificate "
                "or set your Firebase project ID as an app option. Alternatively set the "
                "GOOGLE_CLOUD_PROJECT environment variable."
            )

        header, payload = self._decode_unverified(token)
        issuer = payload.get("iss")
        audience = payload.get("aud")
        subject = payload.get("sub")
        expected_issuer = self.issuer + self.project_id

        project_id_match_msg = (
            f"Make sure the {self.short_name} comes from the same Firebase project as the service account used "
            "to authenticate this SDK."
        )
        verify_id_token_msg = f"See {self.url} for details on how to retrieve {self.short_name}."

        emulated = _auth_utils.is_emulated()

        error_message = None
        if audience == _token_gen.FIREBASE_AUDIENCE:
            error_message = f"{self.operation} expects {self.articled_short_name}, but was given a custom token."
        elif not emulated and not header.get("kid"):
            if (
                header.get("alg") == "HS256"
                and payload.get("v") == 0
                and "uid" in payload.get("d", {})
            ):
                error_message = f"{self.operation} expects {self.articled_short_name}, but was given a legacy custom token."
            else:
                error_message = f'Firebase {self.short_name} has no "kid" claim.'
        elif not emulated and header.get("alg") != "RS256":
            error_message = (
                'Firebase {} has incorrect algorithm. Expected "RS256" but got "{}". {}'.format(
                    self.short_name, header.get("alg"), verify_id_token_msg
                )
            )
        elif not emulated and self.expected_audience and self.expected_audience not in audience:
            error_message = (
                f'Firebase {self.short_name} has incorrect "aud" (audience) claim. Expected "{self.expected_audience}" but '
                f'got "{audience}". {project_id_match_msg} {verify_id_token_msg}'
            )
        elif not emulated and not self.expected_audience and audience != self.project_id:
            error_message = (
                f'Firebase {self.short_name} has incorrect "aud" (audience) claim. Expected "{self.project_id}" but '
                f'got "{audience}". {project_id_match_msg} {verify_id_token_msg}'
            )
        elif issuer != expected_issuer:
            error_message = (
                f'Firebase {self.short_name} has incorrect "iss" (issuer) claim. Expected "{expected_issuer}" but '
                f'got "{issuer}". {project_id_match_msg} {verify_id_token_msg}'
            )
        elif subject is None or not isinstance(subject, str):
            error_message = (
                f'Firebase {self.short_name} has no "sub" (subject) claim. {verify_id_token_msg}'
            )
        elif not subject:
            error_message = f'Firebase {self.short_name} has an empty string "sub" (subject) claim. {verify_id_token_msg}'
        elif len(subject) > 128:
            error_message = f'Firebase {self.short_name} has a "sub" (subject) claim longer than 128 characters. {verify_id_token_msg}'

        if error_message:
            raise self._invalid_token_error(error_message)

        try:
            if emulated:
                verified_claims = payload
            else:
                verified_claims = google.oauth2.id_token.verify_token(
                    token,
                    request=request,
                    # If expected_audience is set then we have already verified
                    # the audience above.
                    audience=(None if self.expected_audience else self.project_id),
                    certs_url=self.cert_url,
                )
            verified_claims["uid"] = verified_claims["sub"]
            return verified_claims
        except google.auth.exceptions.TransportError as error:
            raise _token_gen.CertificateFetchError(str(error), cause=error)  # noqa: B904
        except ValueError as error:
            if "Token expired" in str(error):
                raise self._expired_token_error(str(error), cause=error)  # noqa: B904
            raise self._invalid_token_error(str(error), cause=error)  # noqa: B904

    def _decode_unverified(self, token):
        try:
            header = jwt.decode_header(token)
            payload = jwt.decode(token, verify=False)
            return header, payload
        except ValueError as error:
            raise self._invalid_token_error(str(error), cause=error)  # noqa: B904


class InvalidAuthBlockingTokenError(exceptions.InvalidArgumentError):
    """The provided auth blocking token is not a token."""

    default_message = "The provided auth blocking token is invalid"

    def __init__(self, message, cause=None, http_response=None):
        exceptions.InvalidArgumentError.__init__(self, message, cause, http_response)


class ExpiredAuthBlockingTokenError(InvalidAuthBlockingTokenError):
    """The provided auth blocking token is expired."""

    def __init__(self, message, cause):
        InvalidAuthBlockingTokenError.__init__(self, message, cause)


class AuthBlockingTokenVerifier(_token_gen.TokenVerifier):
    """Verifies auth blocking tokens."""

    def __init__(self, app):
        super().__init__(app)
        self.auth_blocking_token_verifier = _JWTVerifier(
            project_id=app.project_id,
            short_name="Auth Blocking token",
            operation="verify_auth_blocking_token()",
            doc_url="https://cloud.google.com/identity-platform/docs/blocking-functions",
            cert_url=_token_gen.ID_TOKEN_CERT_URI,
            issuer=_token_gen.ID_TOKEN_ISSUER_PREFIX,
            invalid_token_error=InvalidAuthBlockingTokenError,
            expired_token_error=ExpiredAuthBlockingTokenError,
            expected_audience="run.app",  # v2 only
        )

    def verify_auth_blocking_token(self, auth_blocking_token):
        return self.auth_blocking_token_verifier.verify(
            auth_blocking_token,
            self.request,
        )


def verify_auth_blocking_token(auth_blocking_token):
    """Verifies the provided auth blocking token."""
    if _DEFAULT_APP_NAME not in _apps:
        initialize_app()
    return AuthBlockingTokenVerifier(get_app()).verify_auth_blocking_token(auth_blocking_token)
