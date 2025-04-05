"""
Tests for the https module.
"""

import unittest
from flask import Flask, Request
from werkzeug.test import EnvironBuilder

from firebase_functions import core, https_fn


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

        @https_fn.on_request()
        def func(_):
            pass

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {
                        "test": "value"
                    },
                },
            ).get_environ()
            request = Request(environ)

            func(request)

        self.assertEqual(hello, "world")

    def test_on_call_calls_init_function(self):
        app = Flask(__name__)

        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        @https_fn.on_call()
        def func(_):
            pass

        with app.test_request_context("/"):
            environ = EnvironBuilder(
                method="POST",
                json={
                    "data": {
                        "test": "value"
                    },
                },
            ).get_environ()
            request = Request(environ)
            func(request)

        self.assertEqual("world", hello)

    def test_callable_encoding(self):
        app = Flask(__name__)

        @https_fn.on_call()
        def add(req: https_fn.CallableRequest[int]):
            return req.data + 1

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST", json={
                "data": 1
            }).get_environ()
            request = Request(environ)

            response = add(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {"result": 2})

    def test_callable_errors(self):
        app = Flask(__name__)

        @https_fn.on_call()
        def throw_generic_error(req):
            # pylint: disable=broad-exception-raised
            raise Exception("Invalid type")

        @https_fn.on_call()
        def throw_access_denied(req):
            raise https_fn.HttpsError(
                https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                "Permission is denied")

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST", json={
                "data": None
            }).get_environ()
            request = Request(environ)

            response = throw_generic_error(request)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.get_json(),
                {"error": {
                    "message": "INTERNAL",
                    "status": "INTERNAL"
                }})

            response = throw_access_denied(request)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.get_json(), {
                    "error": {
                        "message": "Permission is denied",
                        "status": "PERMISSION_DENIED"
                    }
                })

    def test_yielding_without_streaming(self):
        app = Flask(__name__)

        @https_fn.on_call()
        def yielder(req: https_fn.CallableRequest[int]):
            yield from range(req.data)
            return "OK"

        @https_fn.on_call()
        def yield_thrower(req: https_fn.CallableRequest[int]):
            yield from range(req.data)
            raise https_fn.HttpsError(
                https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                "Can't read anymore")

        @https_fn.on_call()
        def legacy_yielder(req: https_fn.CallableRequest[int]):
            yield from range(req.data)
            # Prior to Python 3.3, this was the way "return" was handled
            # Python 3.5 made this messy however because it converts
            # raised StopIteration into a RuntimeError
            # pylint: disable=stop-iteration-return
            raise StopIteration("OK")

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST", json={
                "data": 5
            }).get_environ()

            request = Request(environ)
            response = yielder(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {"result": "OK"})

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST", json={
                "data": 5
            }).get_environ()

            request = Request(environ)
            response = legacy_yielder(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {"result": "OK"})

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST", json={
                "data": 3
            }).get_environ()

            request = Request(environ)
            response = yield_thrower(request)

            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.get_json(), {
                    "error": {
                        "message": "Can't read anymore",
                        "status": "PERMISSION_DENIED"
                    }
                })

    def test_yielding_with_streaming(self):
        app = Flask(__name__)

        @https_fn.on_call()
        def yielder(req: https_fn.CallableRequest[int]):
            yield from range(req.data)
            return "OK"

        @https_fn.on_call()
        def yield_thrower(req: https_fn.CallableRequest[int]):
            yield from range(req.data)
            raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INTERNAL,
                                      "Throwing")

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST",
                                     json={
                                         "data": 2
                                     },
                                     headers={
                                         "accept": "text/event-stream"
                                     }).get_environ()

            request = Request(environ)
            response = yielder(request)

            self.assertEqual(response.status_code, 200)
            chunks = list(response.response)
            self.assertEqual(chunks, [
                'data: {"message": 0}\n\n', 'data: {"message": 1}\n\n',
                'data: {"result": "OK"}\n\n', "END"
            ])

        with app.test_request_context("/"):
            environ = EnvironBuilder(method="POST",
                                     json={
                                         "data": 2
                                     },
                                     headers={
                                         "accept": "text/event-stream"
                                     }).get_environ()

            request = Request(environ)
            response = yield_thrower(request)

            self.assertEqual(response.status_code, 200)
            chunks = list(response.response)
            self.assertEqual(chunks, [
                'data: {"message": 0}\n\n', 'data: {"message": 1}\n\n',
                'error: {"error": {"status": "INTERNAL", "message": "Throwing"}}\n\n',
                "END"
            ])
