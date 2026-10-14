"""
Identity function tests.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, identity_fn
from firebase_functions.private import _identity_fn

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

    def test_calls_init_function(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        with (
            patch.object(_identity_fn, "_token_verifier", token_verifier_mock),
            patch.object(_identity_fn._firebase_admin, "get_app", return_value=app_mock),
        ):
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

    def test_handler_receives_auth_type_and_resource(self):
        received = None

        def func(event):
            nonlocal received
            received = event

        with (
            patch.object(_identity_fn, "_token_verifier", token_verifier_mock),
            patch.object(_identity_fn._firebase_admin, "get_app", return_value=app_mock),
        ):
            app = Flask(__name__)
            with app.test_request_context("/"):
                environ = EnvironBuilder(
                    method="POST",
                    json={"data": {"jwt": "jwt"}},
                ).get_environ()
                response = identity_fn.before_user_signed_in()(func)(Request(environ))

        self.assertEqual(200, response.status_code)
        self.assertEqual("USER", received.auth_type)
        self.assertEqual(
            identity_fn.AuthBlockingResource(
                service="identitytoolkit.googleapis.com",
                name="projects/project-id",
            ),
            received.resource,
        )


app_mock = Mock(project_id="project-id")


class TestAuthBlockingEventFromTokenData(unittest.TestCase):
    """
    Tests for building an AuthBlockingEvent from a decoded blocking token.
    """

    def _event(self, **token_fields):
        token_data = {
            **token_verifier_mock.verify_auth_blocking_token.return_value,
            **token_fields,
        }
        with patch.object(_identity_fn._firebase_admin, "get_app", return_value=app_mock):
            return _identity_fn._auth_blocking_event_from_token_data(
                _identity_fn.event_type_before_sign_in, token_data
            )

    def test_auth_type_is_user_when_token_has_user_record(self):
        self.assertEqual("USER", self._event().auth_type)

    def test_resource_names_project_when_token_has_no_tenant(self):
        self.assertEqual(
            identity_fn.AuthBlockingResource(
                service="identitytoolkit.googleapis.com",
                name="projects/project-id",
            ),
            self._event().resource,
        )

    def test_resource_names_tenant_when_token_has_tenant_id(self):
        self.assertEqual(
            identity_fn.AuthBlockingResource(
                service="identitytoolkit.googleapis.com",
                name="projects/project-id/tenants/tenant-1",
            ),
            self._event(tenant_id="tenant-1").resource,
        )
