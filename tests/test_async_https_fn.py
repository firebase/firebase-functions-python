"""
Tests for the async https module.
"""

import asyncio
import json
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

from firebase_functions import core
from firebase_functions.aio import https_fn
from firebase_functions.https_fn import CallableRequest, FunctionsErrorCode, HttpsError
from firebase_functions.options import CorsOptions


# Mock Starlette for tests
class MockStarletteResponse:
    def __init__(self, content=None, status_code=200):
        self.content = content
        self.status_code = status_code
        self.headers = {}

class MockJSONResponse(MockStarletteResponse):
    def __init__(self, content, status_code=200):
        super().__init__(json.dumps(content), status_code)
        self.headers["content-type"] = "application/json"


class TestAsyncHttps(unittest.TestCase):
    """
    Tests for the async http module.
    """

    def test_on_request_decorator_validates_async_function(self):
        """Test that on_request requires an async function."""
        # Should raise TypeError for non-async function
        with self.assertRaises(TypeError) as cm:

            @https_fn.on_request()
            def sync_func(request):
                return "sync"

        self.assertIn("requires an async function", str(cm.exception))
        self.assertIn("sync_func is not async", str(cm.exception))

    def test_on_call_decorator_validates_async_function(self):
        """Test that on_call requires an async function."""
        # Should raise TypeError for non-async function
        with self.assertRaises(TypeError) as cm:

            @https_fn.on_call()
            def sync_func(request):
                return "sync"

        self.assertIn("requires an async function", str(cm.exception))
        self.assertIn("sync_func is not async", str(cm.exception))

    def test_on_request_decorator_accepts_async_function(self):
        """Test that on_request accepts async functions."""

        # Should not raise for async function
        @https_fn.on_request()
        async def async_func(request):
            return {"message": "async"}

        # Check that the function is decorated properly
        self.assertTrue(hasattr(async_func, "__firebase_endpoint__"))
        endpoint = async_func.__firebase_endpoint__
        self.assertEqual(endpoint.asgi, True)
        self.assertEqual(endpoint.entryPoint, "async_func")

    def test_on_call_decorator_accepts_async_function(self):
        """Test that on_call accepts async functions."""

        # Should not raise for async function
        @https_fn.on_call()
        async def async_callable(request):
            return {"message": "async"}

        # Check that the function is decorated properly
        self.assertTrue(hasattr(async_callable, "__firebase_endpoint__"))
        endpoint = async_callable.__firebase_endpoint__
        self.assertEqual(endpoint.asgi, True)
        self.assertEqual(endpoint.entryPoint, "async_callable")
        self.assertIsNotNone(endpoint.callableTrigger)

    def test_async_on_request_calls_init_function(self):
        """Test that async on_request calls the init function."""
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = AsyncMock(__name__="example_func")
        func.return_value = {"result": "test"}

        with patch.dict(sys.modules, {
            'starlette': Mock(),
            'starlette.responses': Mock(Response=MockStarletteResponse, JSONResponse=MockJSONResponse)
        }):
            @https_fn.on_request()
            async def decorated_func(request):
                return await func(request)

            # Create a mock request
            mock_request = Mock()

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(decorated_func(mock_request))
            finally:
                loop.close()

            self.assertEqual(hello, "world")
            func.assert_called_once_with(mock_request)

    def test_on_request_with_options(self):
        """Test that on_request passes options correctly."""

        @https_fn.on_request(
            region="us-central1",
            memory=512,
            timeout_sec=60,
        )
        async def async_func(request):
            return {"message": "async"}

        endpoint = async_func.__firebase_endpoint__
        self.assertEqual(endpoint.asgi, True)
        self.assertEqual(endpoint.region, ["us-central1"])
        self.assertEqual(endpoint.availableMemoryMb, 512)
        self.assertEqual(endpoint.timeoutSeconds, 60)

    def test_on_call_with_options(self):
        """Test that on_call passes options correctly."""

        @https_fn.on_call(
            region="europe-west1",
            enforce_app_check=True,
        )
        async def async_callable(request):
            return {"message": "async"}

        endpoint = async_callable.__firebase_endpoint__
        self.assertEqual(endpoint.asgi, True)
        self.assertEqual(endpoint.region, ["europe-west1"])
        # Note: enforce_app_check is not stored in the endpoint directly

    def test_async_on_call_handler(self):
        """Test that async on_call handler works correctly."""

        # Patch starlette imports
        with patch.dict(sys.modules, {
            'starlette': Mock(),
            'starlette.responses': Mock(Response=MockStarletteResponse, JSONResponse=MockJSONResponse)
        }):
            @https_fn.on_call()
            async def async_callable(request: CallableRequest):
                await asyncio.sleep(0.01)  # Simulate async work
                return {"message": "Hello " + request.data.get("name", "World")}

            # Create a mock Starlette request with proper structure
            mock_request = AsyncMock()
            mock_request.method = "POST"
            mock_request.headers = {
                "content-type": "application/json",
            }
            mock_request.body = AsyncMock(return_value=b'{"data": {"name": "Alice"}}')

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(async_callable(mock_request))
                # Response should be a JSONResponse with proper structure
                self.assertEqual(response.status_code, 200)
                # Note: In real test we'd need to check response body content
            finally:
                loop.close()

    def test_async_on_request_cors_preflight(self):
        """Test that async on_request handles CORS preflight correctly."""

        with patch.dict(sys.modules, {
            'starlette': Mock(),
            'starlette.responses': Mock(Response=MockStarletteResponse, JSONResponse=MockJSONResponse)
        }):
            @https_fn.on_request(cors=CorsOptions(cors_origins=["https://example.com"], cors_methods=["GET", "POST"]))
            async def async_func(request):
                return {"message": "Hello"}

            # Create a mock OPTIONS request
            mock_request = Mock()
            mock_request.method = "OPTIONS"

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(async_func(mock_request))
                # Response should have CORS headers
                self.assertEqual(response.status_code, 200)
                self.assertIn("Access-Control-Allow-Origin", response.headers)
                self.assertIn("Access-Control-Allow-Methods", response.headers)
            finally:
                loop.close()

    def test_async_on_call_cors_headers(self):
        """Test that async on_call adds CORS headers correctly."""

        with patch.dict(sys.modules, {
            'starlette': Mock(),
            'starlette.responses': Mock(Response=MockStarletteResponse, JSONResponse=MockJSONResponse)
        }):
            @https_fn.on_call(cors=CorsOptions(cors_origins="*"))
            async def async_callable(request: CallableRequest):
                return {"result": "success"}

            # Create a mock OPTIONS request for preflight
            mock_request = AsyncMock()
            mock_request.method = "OPTIONS"

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(async_callable(mock_request))
                # Response should have CORS headers
                self.assertEqual(response.status_code, 200)
                self.assertIn("Access-Control-Allow-Origin", response.headers)
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
            finally:
                loop.close()

    def test_async_on_call_error_handling(self):
        """Test that async on_call handles HttpsError correctly."""

        with patch.dict(sys.modules, {
            'starlette': Mock(),
            'starlette.responses': Mock(Response=MockStarletteResponse, JSONResponse=MockJSONResponse)
        }):
            @https_fn.on_call()
            async def async_callable(request: CallableRequest):
                raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, "Bad input", {"field": "name"})

            # Create a mock request
            mock_request = AsyncMock()
            mock_request.method = "POST"
            mock_request.headers = {"content-type": "application/json"}
            mock_request.body = AsyncMock(return_value=b'{"data": {}}')

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(async_callable(mock_request))
                # Response should be error with proper status
                self.assertEqual(response.status_code, 400)  # INVALID_ARGUMENT maps to 400
            finally:
                loop.close()

    def test_re_exported_types(self):
        """Test that common types are re-exported from aio.https_fn."""
        # Check that types are available
        self.assertEqual(https_fn.HttpsError, HttpsError)
        self.assertEqual(https_fn.FunctionsErrorCode, FunctionsErrorCode)
        self.assertEqual(https_fn.CallableRequest, CallableRequest)

    def test_multiple_async_functions_in_same_module(self):
        """Test that multiple async functions can be defined in the same module."""

        @https_fn.on_request()
        async def func1(request):
            return {"function": "1"}

        @https_fn.on_request()
        async def func2(request):
            return {"function": "2"}

        @https_fn.on_call()
        async def func3(request):
            return {"function": "3"}

        # Check that all functions have proper endpoints
        self.assertEqual(func1.__firebase_endpoint__.entryPoint, "func1")
        self.assertEqual(func2.__firebase_endpoint__.entryPoint, "func2")
        self.assertEqual(func3.__firebase_endpoint__.entryPoint, "func3")

        # All should have asgi=True
        self.assertTrue(func1.__firebase_endpoint__.asgi)
        self.assertTrue(func2.__firebase_endpoint__.asgi)
        self.assertTrue(func3.__firebase_endpoint__.asgi)


if __name__ == "__main__":
    unittest.main()
