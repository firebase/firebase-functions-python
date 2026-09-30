# Copyright 2026 Google Inc.
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
Tests for auth blocking token verification.
"""

import base64
import datetime
import json
import time

import firebase_admin
import google.oauth2.id_token
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from firebase_functions.private import token_verifier

PROJECT_ID = "test-project"
KEY_ID = "test-key-id"
RUN_APP_AUDIENCE = "https://before-create-7kndfybk7q-ue.a.run.app"
CLOUDFUNCTIONS_AUDIENCE = f"https://us-east1-{PROJECT_ID}.cloudfunctions.net/before_create"


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def _signing_certs(monkeypatch, signing_key):
    """Serve the test signing key in place of Google's public certs."""
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(signing_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(signing_key, hashes.SHA256())
    )
    certs = {KEY_ID: certificate.public_bytes(serialization.Encoding.PEM).decode()}
    monkeypatch.setattr(google.oauth2.id_token, "_fetch_certs", lambda request, certs_url: certs)


@pytest.fixture(autouse=True)
def app():
    app = firebase_admin.initialize_app(
        options={"projectId": PROJECT_ID}, name="token-verifier-test"
    )
    yield app
    firebase_admin.delete_app(app)


def _segment(value: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


def _token(signing_key, audience: str, issuer: str | None = None) -> str:
    header = {"alg": "RS256", "kid": KEY_ID, "typ": "JWT"}
    payload = {
        "aud": audience,
        "iss": issuer or f"https://securetoken.google.com/{PROJECT_ID}",
        "sub": "uid123",
        "iat": int(time.time()) - 10,
        "exp": int(time.time()) + 3600,
        "event_type": "beforeCreate",
    }
    signing_input = f"{_segment(header)}.{_segment(payload)}"
    signature = signing_key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def _verify(app, token: str):
    return token_verifier.AuthBlockingTokenVerifier(app).verify_auth_blocking_token(token)


@pytest.mark.parametrize("audience", [RUN_APP_AUDIENCE, CLOUDFUNCTIONS_AUDIENCE])
def test_accepts_both_audience_forms(app, signing_key, audience):
    assert _verify(app, _token(signing_key, audience))["uid"] == "uid123"


@pytest.mark.parametrize(
    "audience",
    [
        "https://us-east1-other-project.cloudfunctions.net/before_create",
        f"https://us-east1-{PROJECT_ID}.cloudfunctions.net.example.com/before_create",
        "https://example.com/before_create",
    ],
)
def test_rejects_foreign_audience(app, signing_key, audience):
    with pytest.raises(token_verifier.InvalidAuthBlockingTokenError, match='"aud"'):
        _verify(app, _token(signing_key, audience))


def test_rejects_wrong_issuer(app, signing_key):
    token = _token(signing_key, RUN_APP_AUDIENCE, issuer="https://securetoken.google.com/other")
    with pytest.raises(token_verifier.InvalidAuthBlockingTokenError, match='"iss"'):
        _verify(app, token)


def test_rejects_token_signed_by_another_key(app):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(token_verifier.InvalidAuthBlockingTokenError, match="signature"):
        _verify(app, _token(other_key, CLOUDFUNCTIONS_AUDIENCE))
