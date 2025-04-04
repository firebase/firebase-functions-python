"""
Identity function tests.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, Request
from werkzeug.test import EnvironBuilder

token_verifier_mock = MagicMock()
token_verifier_mock.verify_auth_blocking_token = Mock(
    return_value={
        "user_record": {
            "uid": "uid",
            "metadata": {
                "creation_time": 0
            },
            "provider_data": []
        },
        "event_id": "event_id",
        "ip_address": "ip_address",
        "user_agent": "user_agent",
        "iat": 0
    })

firebase_admin_mock = MagicMock()
firebase_admin_mock.initialize_app = Mock()
firebase_admin_mock.get_app = Mock()

mocked_modules = {
    "firebase_functions.private.token_verifier": token_verifier_mock,
    "firebase_admin": firebase_admin_mock
}


class TestIdentity(unittest.TestCase):
    """
    Identity function tests.
    """

    def test_calls_init_function(self):
        hello = None

        with patch.dict("sys.modules", mocked_modules):
            from firebase_functions import core, identity_fn

            @core.init
            def init():
                nonlocal hello
                hello = "world"

            app = Flask(__name__)

            func = Mock(__name__="example_func",
                        return_value=identity_fn.BeforeSignInResponse())

            with app.test_request_context("/"):
                environ = EnvironBuilder(
                    method="POST",
                    json={
                        "data": {
                            "jwt": "jwt"
                        },
                    },
                ).get_environ()
                request = Request(environ)
                decorated_func = identity_fn.before_user_signed_in()(func)
                decorated_func(request)

        self.assertEqual("world", hello)

    def test_auth_blocking_event_from_token_data_email(self):
        """Test parsing a beforeSendEmail event."""
        # Mock token data for email event
        token_data = {
            "iss": "https://securetoken.google.com/project_id",
            "aud": "https://us-east1-project_id.cloudfunctions.net/function-1",
            "iat": 1,  # Unix timestamp
            "exp": 60 * 60 + 1,
            "event_id": "EVENT_ID",
            "event_type": "beforeSendEmail",
            "user_agent": "USER_AGENT",
            "ip_address": "1.2.3.4",
            "locale": "en",
            "recaptcha_score": 0.9,
            "email_type": "PASSWORD_RESET",
            "email": "johndoe@gmail.com"
        }

        with patch.dict("sys.modules", mocked_modules):
            from firebase_functions.private._identity_fn import _auth_blocking_event_from_token_data
            from firebase_functions.private._identity_fn_event_types import event_type_before_email_sent
            import datetime

            event = _auth_blocking_event_from_token_data(
                token_data, event_type_before_email_sent)

        self.assertEqual(event.event_id, "EVENT_ID")
        self.assertEqual(event.ip_address, "1.2.3.4")
        self.assertEqual(event.user_agent, "USER_AGENT")
        self.assertEqual(event.locale, "en")
        self.assertEqual(event.email_type, "PASSWORD_RESET")
        self.assertEqual(event.sms_type, None)
        self.assertEqual(event.data, None)  # No user record for email events
        self.assertEqual(event.timestamp, datetime.datetime.fromtimestamp(1))

        self.assertEqual(event.additional_user_info.email, "johndoe@gmail.com")
        self.assertEqual(event.additional_user_info.recaptcha_score, 0.9)
        self.assertEqual(event.additional_user_info.is_new_user, False)
        self.assertEqual(event.additional_user_info.phone_number, None)

    def test_auth_blocking_event_from_token_data_sms(self):
        """Test parsing a beforeSendSms event."""
        import datetime

        token_data = {
            "iss": "https://securetoken.google.com/project_id",
            "aud": "https://us-east1-project_id.cloudfunctions.net/function-1",
            "iat": 1,  # Unix timestamp
            "exp": 60 * 60 + 1,
            "event_id": "EVENT_ID",
            "event_type": "beforeSendSms",
            "user_agent": "USER_AGENT",
            "ip_address": "1.2.3.4",
            "locale": "en",
            "recaptcha_score": 0.9,
            "sms_type": "SIGN_IN_OR_SIGN_UP",
            "phone_number": "+11234567890"
        }

        with patch.dict("sys.modules", mocked_modules):
            from firebase_functions.private._identity_fn import _auth_blocking_event_from_token_data
            from firebase_functions.private._identity_fn_event_types import event_type_before_sms_sent

            event = _auth_blocking_event_from_token_data(
                token_data, event_type_before_sms_sent)

        self.assertEqual(event.event_id, "EVENT_ID")
        self.assertEqual(event.ip_address, "1.2.3.4")
        self.assertEqual(event.user_agent, "USER_AGENT")
        self.assertEqual(event.locale, "en")
        self.assertEqual(event.email_type, None)
        self.assertEqual(event.sms_type, "SIGN_IN_OR_SIGN_UP")
        self.assertEqual(event.data, None)  # No user record for SMS events
        self.assertEqual(event.timestamp, datetime.datetime.fromtimestamp(1))

        self.assertEqual(event.additional_user_info.phone_number,
                         "+11234567890")
        self.assertEqual(event.additional_user_info.recaptcha_score, 0.9)
        self.assertEqual(event.additional_user_info.is_new_user, False)
        self.assertEqual(event.additional_user_info.email, None)
