"""
Tests for the https module.
"""

import re
import unittest
from unittest.mock import Mock

from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, https_fn
from firebase_functions.options import CorsOptions


class TestHttps(unittest.TestCase):
    """
    Tests for the http module.
    """

    def test_on_request_calls_init_function(self):
        app = Flask(__name__)

        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = Mock(__name__="example_func")

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {"test": "value"},
                },
            ).get_environ()
            request = Request(environ)
            decorated_func = https_fn.on_request()(func)

            decorated_func(request)

        self.assertEqual(hello, "world")

    def test_on_request_calls_init_function_with_cors(self):
        app = Flask(__name__)

        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = Mock(__name__="example_func", return_value="OK")

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {"test": "value"},
                },
            ).get_environ()
            request = Request(environ)
            decorated_func = https_fn.on_request(
                cors=CorsOptions(cors_origins="*", cors_methods="GET")
            )(func)

            decorated_func(request)

        self.assertEqual(hello, "world")

    def test_on_call_calls_init_function(self):
        app = Flask(__name__)

        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = Mock(__name__="example_func")

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {"test": "value"},
                },
            ).get_environ()
            request = Request(environ)
            decorated_func = https_fn.on_call()(func)

            decorated_func(request)

        self.assertEqual("world", hello)

    def test_https_error_passes_message_to_super(self):
        """
        HttpsError should pass the message to the base Exception so that
        str(err) and err.args contain the message.
        """
        err = https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="something went wrong",
        )

        self.assertEqual(str(err), "something went wrong")
        self.assertEqual(err.args, ("something went wrong",))

    def test_on_request_cors_options_branches(self):
        """
        CorsOptions with either or both fields unset should fall back to
        flask-cors defaults on preflight requests instead of passing None.
        """
        cases = [
            (
                CorsOptions(cors_origins="https://example.com", cors_methods=["GET", "POST"]),
                "https://example.com",
                "https://example.com",
                {"GET", "POST"},
            ),
            (
                CorsOptions(cors_origins="https://example.com"),
                "https://example.com",
                "https://example.com",
                {"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"},
            ),
            (
                CorsOptions(cors_methods=["GET"]),
                "https://example.com",
                "https://example.com",
                {"GET"},
            ),
            (
                CorsOptions(),
                "https://example.com",
                "https://example.com",
                {"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"},
            ),
            (
                CorsOptions(cors_origins="https://allowed.example.com"),
                "https://example.com",
                None,
                set(),
            ),
            (
                CorsOptions(
                    cors_origins=re.compile(r"https://.*\.example\.com"),
                    cors_methods=["GET"],
                ),
                "https://sub.example.com",
                "https://sub.example.com",
                {"GET"},
            ),
        ]

        for cors_opts, req_origin, expected_origin, expected_methods in cases:
            with self.subTest(cors=cors_opts, origin=req_origin):
                app = Flask(__name__)

                @https_fn.on_request(cors=cors_opts)
                def handler(_req: Request):
                    return "OK"

                headers = {
                    "Origin": req_origin,
                    "Access-Control-Request-Method": "GET",
                }
                with app.test_request_context("/", method="OPTIONS", headers=headers) as ctx:
                    resp = handler(ctx.request)

                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), expected_origin)
                allow_methods = resp.headers.get("Access-Control-Allow-Methods", "")
                self.assertEqual(
                    {m.strip() for m in allow_methods.split(",") if m.strip()},
                    expected_methods,
                )
