"""
Tests for the https module.
"""

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
