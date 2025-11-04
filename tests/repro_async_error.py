import json

import pytest
from flask import Request, Response

from firebase_functions import https_fn


# Mock request object
class MockRequest:
    def __init__(self, data=None, headers=None, method="POST"):
        self.data = json.dumps(data).encode("utf-8") if data else b""
        self.headers = headers or {"Content-Type": "application/json"}
        self.method = method
        self.json = data


# Async function with error
@https_fn.on_request()
async def async_error_func(req: Request) -> Response:
    raise ValueError("Async error")


# Sync function with error
@https_fn.on_request()
def sync_error_func(req: Request) -> Response:
    raise ValueError("Sync error")


@pytest.mark.asyncio
async def test_async_error_handling():
    req = MockRequest()
    try:
        await async_error_func(req)
    except ValueError as e:
        assert str(e) == "Async error"
    except Exception as e:
        pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")


def test_sync_error_handling():
    req = MockRequest()
    try:
        sync_error_func(req)
    except ValueError as e:
        assert str(e) == "Sync error"
    except Exception as e:
        pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")
