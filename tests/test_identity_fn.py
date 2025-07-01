"""
Identity function tests.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, identity_fn

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
mocked_modules = {
    "firebase_functions.private.token_verifier": token_verifier_mock,
}


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

        with patch.dict("sys.modules", mocked_modules):
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
