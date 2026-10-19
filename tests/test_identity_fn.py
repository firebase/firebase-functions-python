"""
Identity function tests.
"""

import datetime as dt
import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml
from cloudevents.http import CloudEvent
from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, identity_fn, params
from firebase_functions.private import _identity_fn, serving

token_verifier_mock = MagicMock()
token_verifier_mock.verify_auth_blocking_token = Mock(
    return_value={
        "user_record": {"uid": "uid", "metadata": {"creation_time": 0}, "provider_data": []},
        "event_id": "event_id",
        "ip_address": "ip_address",
        "user_agent": "user_agent",
        "iat": 0,
    }
)


class TestIdentity(unittest.TestCase):
    """
    Identity function tests.
    """

    def tearDown(self) -> None:
        core._init_callback = None
        core._did_init = False

    def test_calls_init_function(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        with patch.object(_identity_fn, "_token_verifier", token_verifier_mock):
            app = Flask(__name__)

            func = Mock(__name__="example_func", return_value=identity_fn.BeforeSignInResponse())

            with app.test_request_context("/"):
                environ = EnvironBuilder(
                    method="POST",
                    json={
                        "data": {"jwt": "jwt"},
                    },
                ).get_environ()
                request = Request(environ)
                decorated_func = identity_fn.before_user_signed_in()(func)
                decorated_func(request)

        self.assertEqual("world", hello)

    def test_on_user_created_endpoint_metadata(self) -> None:
        @identity_fn.on_user_created()
        def example(_event: identity_fn.AuthEvent) -> None:
            pass

        endpoint = getattr(example, "__firebase_endpoint__", None)
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.entryPoint, "example")
        self.assertEqual(
            endpoint.eventTrigger,
            {
                "eventType": "google.firebase.auth.user.v2.created",
                "eventFilters": {},
                "retry": False,
                "region": "global",
            },
        )

    def test_on_user_deleted_endpoint_metadata(self) -> None:
        @identity_fn.on_user_deleted()
        def example(_event: identity_fn.AuthEvent) -> None:
            pass

        endpoint = getattr(example, "__firebase_endpoint__", None)
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.entryPoint, "example")
        self.assertEqual(
            endpoint.eventTrigger,
            {
                "eventType": "google.firebase.auth.user.v2.deleted",
                "eventFilters": {},
                "retry": False,
                "region": "global",
            },
        )

    def test_on_user_created_tenant_id_filter(self) -> None:
        @identity_fn.on_user_created(tenant_id="my-tenant")
        def example(_event: identity_fn.AuthEvent) -> None:
            pass

        endpoint = getattr(example, "__firebase_endpoint__", None)
        assert endpoint is not None
        self.assertEqual(endpoint.eventTrigger["eventFilters"], {"tenantid": "my-tenant"})

        with self.assertRaises(ValueError):

            @identity_fn.on_user_created(tenant_id="")
            def _empty_tenant(_event: identity_fn.AuthEvent) -> None:
                pass

    def test_on_user_created_tenant_id_expression(self) -> None:
        tenant_param = params.StringParam("MY_TENANT")

        @identity_fn.on_user_created(tenant_id=tenant_param)
        def example(_event: identity_fn.AuthEvent) -> None:
            pass

        endpoint = getattr(example, "__firebase_endpoint__", None)
        assert endpoint is not None
        self.assertEqual(endpoint.eventTrigger["eventFilters"], {"tenantid": tenant_param})

        rendered_yaml = yaml.safe_load(serving.functions_as_yaml({"example": example}))
        self.assertEqual(
            rendered_yaml["endpoints"]["example"]["eventTrigger"]["eventFilters"],
            {"tenantid": "{{ params.MY_TENANT }}"},
        )

    def test_on_user_created_unpacks_eventarc_value_envelope(self) -> None:
        captured_event: identity_fn.AuthEvent | None = None

        @identity_fn.on_user_created()
        def example(event: identity_fn.AuthEvent) -> None:
            nonlocal captured_event
            captured_event = event

        raw_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-id-123",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.created",
                "time": "2023-01-01T00:00:00Z",
                "tenantid": "my-tenant",
            },
            data={
                "value": {
                    "uid": "1qEveruhwnbiG1B9taHIBMmOVE83",
                    "email": "testuser@example.com",
                    "emailVerified": True,
                    "displayName": "Test User",
                    "photoUrl": "http://example.com/photo.jpg",
                    "phoneNumber": "+15555550100",
                    "disabled": False,
                    "metadata": {
                        "createTime": "2023-01-01T00:00:00Z",
                        "lastSignInTime": "2023-01-02T12:30:00Z",
                    },
                    "providerData": [
                        {
                            "uid": "google-uid",
                            "providerId": "google.com",
                            "displayName": "Google User",
                            "email": "testuser@example.com",
                            "photoUrl": "http://example.com/google.jpg",
                        }
                    ],
                    "customClaims": {"admin": True},
                }
            },
        )

        example(raw_ce)  # type: ignore[arg-type]
        self.assertIsNotNone(captured_event)
        assert captured_event is not None
        self.assertEqual(captured_event.project, "my-project")
        self.assertEqual(captured_event.tenant_id, "my-tenant")
        self.assertIsNotNone(captured_event.data)
        assert captured_event.data is not None
        self.assertEqual(captured_event.data.uid, "1qEveruhwnbiG1B9taHIBMmOVE83")
        self.assertEqual(captured_event.data.email, "testuser@example.com")
        self.assertTrue(captured_event.data.email_verified)
        self.assertEqual(captured_event.data.display_name, "Test User")
        self.assertEqual(captured_event.data.photo_url, "http://example.com/photo.jpg")
        self.assertEqual(captured_event.data.phone_number, "+15555550100")
        self.assertFalse(captured_event.data.disabled)
        self.assertEqual(
            captured_event.data.metadata.creation_time,
            dt.datetime(2023, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(
            captured_event.data.metadata.last_sign_in_time,
            dt.datetime(2023, 1, 2, 12, 30, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(len(captured_event.data.provider_data), 1)
        self.assertEqual(captured_event.data.provider_data[0].uid, "google-uid")
        self.assertEqual(captured_event.data.provider_data[0].provider_id, "google.com")
        self.assertEqual(captured_event.data.provider_data[0].display_name, "Google User")
        self.assertEqual(captured_event.data.provider_data[0].email, "testuser@example.com")
        self.assertEqual(
            captured_event.data.provider_data[0].photo_url, "http://example.com/google.jpg"
        )
        self.assertEqual(captured_event.data.custom_claims, {"admin": True})
        self.assertEqual(captured_event.data.tenant_id, "my-tenant")

    def test_on_user_deleted_unpacks_old_value_envelope(self) -> None:
        captured_event: identity_fn.AuthEvent | None = None

        @identity_fn.on_user_deleted()
        def example(event: identity_fn.AuthEvent) -> None:
            nonlocal captured_event
            captured_event = event

        raw_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-id-del",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.deleted",
                "time": "2023-01-01T00:00:00Z",
            },
            data={
                "value": None,
                "oldValue": {
                    "uid": "deleted-user-uid",
                    "email": "deleted@example.com",
                    "photoURL": "http://example.com/legacy-photo.jpg",
                    "tenantId": "emulator-tenant",
                    "metadata": {
                        "creationTime": "2023-01-01T00:00:00Z",
                    },
                    "providerData": [
                        {
                            "rawId": "github-raw-uid",
                            "providerId": "github.com",
                            "photoURL": "http://example.com/gh.jpg",
                        }
                    ],
                },
            },
        )

        example(raw_ce)  # type: ignore[arg-type]
        self.assertIsNotNone(captured_event)
        assert captured_event is not None
        self.assertEqual(captured_event.project, "my-project")
        self.assertEqual(captured_event.tenant_id, "emulator-tenant")
        assert captured_event.data is not None
        self.assertEqual(captured_event.data.uid, "deleted-user-uid")
        self.assertEqual(captured_event.data.email, "deleted@example.com")
        self.assertEqual(captured_event.data.photo_url, "http://example.com/legacy-photo.jpg")
        self.assertEqual(captured_event.data.tenant_id, "emulator-tenant")
        self.assertEqual(
            captured_event.data.metadata.creation_time,
            dt.datetime(2023, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(len(captured_event.data.provider_data), 1)
        self.assertEqual(captured_event.data.provider_data[0].uid, "github-raw-uid")
        self.assertEqual(captured_event.data.provider_data[0].provider_id, "github.com")
        self.assertEqual(
            captured_event.data.provider_data[0].photo_url, "http://example.com/gh.jpg"
        )

    def test_raises_on_null_or_unrecognized_data(self) -> None:
        captured_events: list[identity_fn.AuthEvent] = []

        @identity_fn.on_user_created()
        def example(event: identity_fn.AuthEvent) -> None:
            captured_events.append(event)

        invalid_payloads: list[object] = [
            None,
            {},
            {"value": None},
            {"value": {}},
            {"unrecognized": "payload"},
            {"value": {"email": "missing-uid@example.com"}},
            {"value": {"uid": "valid-uid", "metadata": {"createTime": "not-a-timestamp"}}},
            {
                "value": {
                    "uid": "valid-uid",
                    "metadata": {
                        "createTime": "2023-01-01T00:00:00Z",
                        "lastSignInTime": "not-a-timestamp",
                    },
                }
            },
        ]
        for invalid_data in invalid_payloads:
            raw_invalid_ce = CloudEvent(
                attributes={
                    "specversion": "1.0",
                    "id": "event-invalid",
                    "source": "//identitytoolkit.googleapis.com/projects/my-project",
                    "type": "google.firebase.auth.user.v2.created",
                    "time": "2023-01-01T00:00:00Z",
                },
                data=invalid_data,
            )
            with self.assertRaises(ValueError):
                example(raw_invalid_ce)  # type: ignore[arg-type]

        raw_invalid_time_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-invalid-time",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.created",
                "time": "not-a-timestamp",
            },
            data={"value": {"uid": "valid-uid"}},
        )
        with self.assertRaises(ValueError):
            example(raw_invalid_time_ce)  # type: ignore[arg-type]

        self.assertEqual(len(captured_events), 0)

    def test_parse_auth_timestamp_handles_out_of_range_numbers(self) -> None:
        self.assertIsNone(_identity_fn._parse_auth_timestamp(1e20))
        self.assertIsNone(_identity_fn._parse_auth_timestamp("99999999999999999999"))
        self.assertIsNone(_identity_fn._parse_auth_timestamp(float("inf")))
        self.assertIsNone(_identity_fn._parse_auth_timestamp(float("nan")))
        self.assertIsNone(_identity_fn._parse_auth_timestamp("²"))

    def test_on_user_created_defaults_and_timezone_normalization(self) -> None:
        captured_event: identity_fn.AuthEvent | None = None

        @identity_fn.on_user_created()
        def example(event: identity_fn.AuthEvent) -> None:
            nonlocal captured_event
            captured_event = event

        raw_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-minimal",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.created",
                "time": "2023-01-01T02:00:00+02:00",
            },
            data={
                "value": {
                    "uid": "minimal-user",
                }
            },
        )

        example(raw_ce)  # type: ignore[arg-type]
        assert captured_event is not None
        self.assertEqual(
            captured_event.time,
            dt.datetime(2023, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(
            captured_event.data.metadata.creation_time,
            dt.datetime(1970, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertIsNone(captured_event.data.metadata.last_sign_in_time)
        self.assertIsNone(captured_event.data.custom_claims)
        self.assertIsNone(captured_event.data.password_hash)
        self.assertIsNone(captured_event.data.password_salt)
        self.assertIsNone(captured_event.data.tokens_valid_after_time)
        self.assertIsNone(captured_event.data.multi_factor)
