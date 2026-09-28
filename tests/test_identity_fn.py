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
# Patch the reference _identity_fn holds rather than the sys.modules entry, which
# `import ... as` bypasses once anything else has imported the real module.


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
