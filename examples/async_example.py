"""Example showing async HTTP functions with firebase-functions-python."""

import asyncio

from flask import Request, Response

from firebase_functions import https_fn
from firebase_functions.aio import https_fn as async_https_fn


# Traditional synchronous function
@https_fn.on_request()
def sync_hello(request: Request) -> Response:
    """A traditional synchronous HTTP function."""
    name = request.args.get("name", "World")
    return Response(f"Hello {name}! (sync)")


# New async function using aio namespace
@async_https_fn.on_request()
async def async_hello(request) -> dict:
    """An async HTTP function that can use await."""
    # Simulate async operation (e.g., database query, API call)
    await asyncio.sleep(0.1)

    # In async functions, request is a Starlette Request object
    name = request.query_params.get("name", "World")

    # Can return dict which will be JSON serialized
    return {"message": f"Hello {name}! (async)", "type": "async"}


# Async callable function
@async_https_fn.on_call()
async def async_callable(request: async_https_fn.CallableRequest) -> dict:
    """An async callable function."""
    # Access the data sent by the client
    name = request.data.get("name", "World")

    # Simulate async work
    await asyncio.sleep(0.1)

    # Access auth information if available
    user_id = request.auth.uid if request.auth else "anonymous"

    return {
        "message": f"Hello {name}!",
        "user": user_id,
        "timestamp": asyncio.get_event_loop().time(),
    }


# Example of mixing sync and async in the same file
@https_fn.on_request()
def list_functions(request: Request) -> Response:
    """List all functions in this module."""
    functions = [
        {"name": "sync_hello", "type": "sync", "url": "/sync_hello"},
        {"name": "async_hello", "type": "async", "url": "/async_hello"},
        {"name": "async_callable", "type": "async_callable", "url": "/async_callable"},
    ]
    return Response(str(functions), content_type="application/json")
