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

from firebase_functions import core, identity_fn, options, params
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
                    "photoURL": "http://example.com/photo.jpg",
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
                            "photoURL": "http://example.com/google.jpg",
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
                "tenantid": "my-tenant",
            },
            data={
                "value": None,
                "oldValue": {
                    "uid": "deleted-user-uid",
                    "email": "deleted@example.com",
                    "photoURL": "http://example.com/legacy-photo.jpg",
                    "metadata": {
                        "createTime": "2023-01-01T00:00:00Z",
                    },
                    "providerData": [
                        {
                            "uid": "github-raw-uid",
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
        self.assertEqual(captured_event.tenant_id, "my-tenant")
        assert captured_event.data is not None
        self.assertEqual(captured_event.data.uid, "deleted-user-uid")
        self.assertEqual(captured_event.data.email, "deleted@example.com")
        self.assertEqual(captured_event.data.photo_url, "http://example.com/legacy-photo.jpg")
        self.assertEqual(captured_event.data.tenant_id, "my-tenant")
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
        self.assertIsNone(captured_event.data.metadata.creation_time)
        self.assertIsNone(captured_event.data.metadata.last_sign_in_time)
        self.assertIsNone(captured_event.data.custom_claims)
        self.assertIsNone(captured_event.data.password_hash)
        self.assertIsNone(captured_event.data.password_salt)
        self.assertIsNone(captured_event.data.tokens_valid_after_time)
        self.assertIsNone(captured_event.data.multi_factor)

    def test_on_user_created_is_not_tenant(self) -> None:
        called_uids: list[str] = []
        init_calls = 0

        @core.init
        def init_fn() -> None:
            nonlocal init_calls
            init_calls += 1

        @identity_fn.on_user_created(tenant_id=identity_fn.IS_NOT_TENANT)
        def example(event: identity_fn.AuthEvent) -> None:
            called_uids.append(event.data.uid)

        endpoint = getattr(example, "__firebase_endpoint__", None)
        assert endpoint is not None
        self.assertEqual(endpoint.eventTrigger["eventFilters"], {})

        rendered_yaml = yaml.safe_load(serving.functions_as_yaml({"example": example}))
        self.assertEqual(
            rendered_yaml["endpoints"]["example"]["eventTrigger"]["eventFilters"],
            {},
        )

        # Should ignore events with top-level tenantid CloudEvent attribute
        # before unpacking the payload (and not run @core.init)
        tenant_attr_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-tenant-attr",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.created",
                "time": "2023-01-01T00:00:00Z",
                "tenantid": "some-tenant",
            },
            data=None,
        )
        example(tenant_attr_ce)  # type: ignore[arg-type]
        self.assertEqual(called_uids, [])
        self.assertEqual(init_calls, 0)

        # Should execute for non-tenant events (and run @core.init)
        non_tenant_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-no-tenant",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.created",
                "time": "2023-01-01T00:00:00Z",
            },
            data={"value": {"uid": "user-no-tenant"}},
        )
        example(non_tenant_ce)  # type: ignore[arg-type]
        self.assertEqual(called_uids, ["user-no-tenant"])
        self.assertEqual(init_calls, 1)

        # Also verify on_user_deleted with IS_NOT_TENANT
        deleted_uids: list[str] = []

        @identity_fn.on_user_deleted(tenant_id=identity_fn.IS_NOT_TENANT)
        def example_deleted(event: identity_fn.AuthEvent) -> None:
            deleted_uids.append(event.data.uid)

        delete_endpoint = getattr(example_deleted, "__firebase_endpoint__", None)
        assert delete_endpoint is not None
        self.assertEqual(delete_endpoint.eventTrigger["eventFilters"], {})

        non_tenant_deleted_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-del-no-tenant",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.deleted",
                "time": "2023-01-01T00:00:00Z",
            },
            data={"value": None, "oldValue": {"uid": "deleted-no-tenant"}},
        )
        tenant_deleted_ce = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "event-del-tenant",
                "source": "//identitytoolkit.googleapis.com/projects/my-project",
                "type": "google.firebase.auth.user.v2.deleted",
                "time": "2023-01-01T00:00:00Z",
                "tenantid": "some-tenant",
            },
            data={"value": None, "oldValue": {"uid": "deleted-with-tenant"}},
        )
        example_deleted(non_tenant_deleted_ce)  # type: ignore[arg-type]
        example_deleted(tenant_deleted_ce)  # type: ignore[arg-type]
        self.assertEqual(deleted_uids, ["deleted-no-tenant"])

        # Rejects other Sentinel instances such as RESET_VALUE
        with self.assertRaises(ValueError):

            @identity_fn.on_user_created(tenant_id=options.RESET_VALUE)  # type: ignore[arg-type]
            def _invalid_sentinel(_event: identity_fn.AuthEvent) -> None:
                pass

    def test_blocking_event_timestamps_are_timezone_aware_utc(self) -> None:
        captured_event: identity_fn.AuthBlockingEvent | None = None

        @identity_fn.before_user_signed_in()
        def example(
            event: identity_fn.AuthBlockingEvent,
        ) -> identity_fn.BeforeSignInResponse | None:
            nonlocal captured_event
            captured_event = event
            return None

        mock_verifier = MagicMock()
        mock_verifier.verify_auth_blocking_token = Mock(
            return_value={
                "user_record": {
                    "uid": "user-123",
                    "metadata": {
                        "creation_time": 1672531200000,
                        "last_sign_in_time": 1672662600000,
                    },
                    "provider_data": [],
                    "tokens_valid_after_time": 1672704000,
                    "multi_factor": {
                        "enrolled_factors": [
                            {
                                "uid": "mfa-1",
                                "factor_id": "phone",
                                "enrollment_time": "2023-01-04T06:15:30.123456789Z",
                                "phone_number": "+15555550100",
                            },
                            {
                                "uid": "mfa-2",
                                "factor_id": "phone",
                                "enrollment_time": "2023-01-04T08:15:30+02:00",
                                "phone_number": "+15555550101",
                            },
                            {
                                "uid": "mfa-3",
                                "factor_id": "phone",
                                "enrollment_time": "",
                                "phone_number": "+15555550102",
                            },
                        ]
                    },
                },
                "event_id": "event-id",
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent",
                "iat": 1672876800,
                "sign_in_method": "google.com",
                "oauth_access_token": "token-abc",
                "oauth_expires_in": 3600,
            }
        )

        with (
            patch.object(_identity_fn, "_token_verifier", mock_verifier),
            patch.object(_identity_fn._time, "time", return_value=1672963200.0),
        ):
            app = Flask(__name__)
            with app.test_request_context("/"):
                environ = EnvironBuilder(
                    method="POST",
                    json={"data": {"jwt": "jwt"}},
                ).get_environ()
                request = Request(environ)
                example(request)  # type: ignore[arg-type]

        self.assertIsNotNone(captured_event)
        assert captured_event is not None
        assert captured_event.data.metadata.creation_time is not None
        self.assertEqual(
            captured_event.data.metadata.creation_time,
            dt.datetime(2023, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(captured_event.data.metadata.creation_time.tzinfo, dt.timezone.utc)

        assert captured_event.data.metadata.last_sign_in_time is not None
        self.assertEqual(
            captured_event.data.metadata.last_sign_in_time,
            dt.datetime(2023, 1, 2, 12, 30, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(captured_event.data.metadata.last_sign_in_time.tzinfo, dt.timezone.utc)

        assert captured_event.data.tokens_valid_after_time is not None
        self.assertEqual(
            captured_event.data.tokens_valid_after_time,
            dt.datetime(2023, 1, 3, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(captured_event.data.tokens_valid_after_time.tzinfo, dt.timezone.utc)

        assert captured_event.data.multi_factor is not None
        factor_0_time = captured_event.data.multi_factor.enrolled_factors[0].enrollment_time
        assert factor_0_time is not None
        self.assertEqual(
            factor_0_time,
            dt.datetime(2023, 1, 4, 6, 15, 30, 123456, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(factor_0_time.tzinfo, dt.timezone.utc)

        factor_1_time = captured_event.data.multi_factor.enrolled_factors[1].enrollment_time
        assert factor_1_time is not None
        self.assertEqual(
            factor_1_time,
            dt.datetime(2023, 1, 4, 6, 15, 30, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(factor_1_time.tzinfo, dt.timezone.utc)

        self.assertIsNone(
            captured_event.data.multi_factor.enrolled_factors[2].enrollment_time,
        )

        self.assertEqual(
            captured_event.timestamp,
            dt.datetime(2023, 1, 5, 0, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(captured_event.timestamp.tzinfo, dt.timezone.utc)

        assert captured_event.credential is not None
        assert captured_event.credential.expiration_time is not None
        self.assertEqual(
            captured_event.credential.expiration_time,
            dt.datetime(2023, 1, 6, 1, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(captured_event.credential.expiration_time.tzinfo, dt.timezone.utc)

        # Verify None/omitted metadata timestamps and Auth Emulator string/omitted oauth_expires_in
        # ("3600", "0", and omitted) via the public @before_user_created() decorator.
        created_events: list[identity_fn.AuthBlockingEvent] = []

        @identity_fn.before_user_created()
        def on_before_create(
            event: identity_fn.AuthBlockingEvent,
        ) -> identity_fn.BeforeCreateResponse | None:
            created_events.append(event)
            return None

        mock_verifier.verify_auth_blocking_token = Mock(
            side_effect=[
                {
                    "user_record": {
                        "uid": "user-emulated-1",
                        "metadata": {"creation_time": None, "last_sign_in_time": None},
                        "provider_data": [],
                    },
                    "event_id": "event-emulated-1",
                    "ip_address": "127.0.0.1",
                    "user_agent": "test-agent",
                    "iat": 1672876800,
                    "sign_in_method": "google.com",
                    "oauth_access_token": "token-abc",
                    "oauth_expires_in": "3600",
                },
                {
                    "user_record": {
                        "uid": "user-emulated-2",
                        "provider_data": [],
                    },
                    "event_id": "event-emulated-2",
                    "ip_address": "127.0.0.1",
                    "user_agent": "test-agent",
                    "iat": 1672876800,
                    "sign_in_method": "google.com",
                    "oauth_access_token": "token-abc",
                    "oauth_expires_in": "0",
                },
                {
                    "user_record": {
                        "uid": "user-emulated-3",
                        "provider_data": [],
                    },
                    "event_id": "event-emulated-3",
                    "ip_address": "127.0.0.1",
                    "user_agent": "test-agent",
                    "iat": 1672876800,
                    "sign_in_method": "google.com",
                    "oauth_access_token": "token-abc",
                },
            ]
        )

        with (
            patch.object(_identity_fn, "_token_verifier", mock_verifier),
            patch.object(_identity_fn._time, "time", return_value=1672963200.0),
        ):
            app = Flask(__name__)
            with app.test_request_context("/"):
                for _ in range(3):
                    environ = EnvironBuilder(
                        method="POST",
                        json={"data": {"jwt": "jwt"}},
                    ).get_environ()
                    on_before_create(Request(environ))  # type: ignore[arg-type]

        self.assertEqual(len(created_events), 3)
        self.assertEqual(
            created_events[0].data.metadata,
            identity_fn.AuthUserMetadata(creation_time=None, last_sign_in_time=None),
        )
        assert created_events[0].credential is not None
        self.assertEqual(
            created_events[0].credential.expiration_time,
            dt.datetime(2023, 1, 6, 1, 0, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(
            created_events[1].data.metadata,
            identity_fn.AuthUserMetadata(creation_time=None, last_sign_in_time=None),
        )
        assert created_events[1].credential is not None
        self.assertIsNone(created_events[1].credential.expiration_time)
        assert created_events[2].credential is not None
        self.assertIsNone(created_events[2].credential.expiration_time)
