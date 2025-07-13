# Async Support for Firebase Functions Python

## Overview

This document outlines the design and implementation plan for adding async function support to firebase-functions-python. The goal is to leverage the new async capabilities in functions-framework while maintaining full backward compatibility with existing sync functions.

## Background

Functions-framework recently added async support via the `--asgi` flag, allowing async functions to be defined like:

```python
import functions_framework.aio

@functions_framework.aio.http
async def hello_async(request):  # Starlette.Request
    await asyncio.sleep(1)
    return "Hello, async world!"
```

## Design Goals

1. **No code duplication** - Reuse existing decorators and logic
2. **Backward compatibility** - All existing sync functions must continue to work
3. **Unified API** - Users shouldn't need different decorators for sync vs async
4. **Type safety** - Proper typing for both sync and async cases
5. **Flexibility** - The aio namespace accepts both sync and async functions
6. **Universal support** - Async should work for ALL function types, not just HTTP

## Function Types to Support

Firebase Functions Python supports multiple trigger types that all need async support:

### 1. HTTP Functions
- `@https_fn.on_request()` - Raw HTTP requests
- `@https_fn.on_call()` - Callable functions with auth/validation

### 2. Firestore Functions
- `@firestore_fn.on_document_created()`
- `@firestore_fn.on_document_updated()`
- `@firestore_fn.on_document_deleted()`
- `@firestore_fn.on_document_written()`

### 3. Realtime Database Functions
- `@db_fn.on_value_created()`
- `@db_fn.on_value_updated()`
- `@db_fn.on_value_deleted()`
- `@db_fn.on_value_written()`

### 4. Cloud Storage Functions
- `@storage_fn.on_object_archived()`
- `@storage_fn.on_object_deleted()`
- `@storage_fn.on_object_finalized()`
- `@storage_fn.on_object_metadata_updated()`

### 5. Pub/Sub Functions
- `@pubsub_fn.on_message_published()`

### 6. Scheduler Functions
- `@scheduler_fn.on_schedule()`

### 7. Task Queue Functions
- `@tasks_fn.on_task_dispatched()`

### 8. EventArc Functions
- `@eventarc_fn.on_custom_event_published()`

### 9. Remote Config Functions
- `@remote_config_fn.on_config_updated()`

### 10. Test Lab Functions
- `@test_lab_fn.on_test_matrix_completed()`

### 11. Alerts Functions
- Various alert triggers for billing, crashlytics, performance, etc.

### 12. Identity Functions
- `@identity_fn.before_user_created()`
- `@identity_fn.before_user_signed_in()`

## Implementation Strategy

### Phase 1: Core Infrastructure

#### 1.1 Async Detection Mechanism
- Add utility function to detect if a function is async using `inspect.iscoroutinefunction()`
- This detection should happen at decoration time

#### 1.2 Metadata Storage
- Extend the `__firebase_endpoint__` attribute to include runtime mode information
- Add a field to `ManifestEndpoint` to indicate async functions:
  ```python
  @dataclasses.dataclass(frozen=True)
  class ManifestEndpoint:
      # ... existing fields ...
      runtime_mode: Literal["sync", "async"] | None = "sync"
  ```

#### 1.3 Type System Updates
- Create type unions to handle both sync and async cases
- For HTTP functions:
  - Sync: `flask.Request` and `flask.Response`
  - Async: `starlette.requests.Request` and response types
- For event functions:
  - Both sync and async will receive the same event objects
  - The difference is whether the handler is async

### Phase 2: Decorator Updates

#### 2.1 Namespace-based Approach
Instead of modifying existing decorators, we created a new `aio` namespace:
- `firebase_functions.aio.https_fn` for async HTTP functions
- The aio decorators accept both sync and async functions
- ASGI runtime handles sync functions by running them in a thread pool

#### 2.2 Shared Implementation
To avoid code duplication, we extracted shared business logic:
- `_validate_on_call_request_headers()` - Validates headers and method
- `_process_on_call_request_body()` - Processes request body after reading
- `_format_on_call_response()` - Formats successful responses
- `_format_on_call_error()` - Formats error responses
- `_add_cors_headers_to_response()` - Adds CORS headers to any response

The decorators use a shared implementation with an `asgi` parameter to differentiate between sync and async modes.

#### 2.2 HTTP Functions Special Handling
HTTP functions need special care because the request type changes:
- Sync: `flask.Request`
- Async: `starlette.requests.Request`

We'll need to handle this in the type system and potentially in request processing.

### Phase 3: Manifest and Deployment

#### 3.1 Manifest Generation
- Update `serving.py` to include runtime mode in the manifest
- The functions.yaml should indicate which functions need async runtime

#### 3.2 Firebase CLI Integration
- The CLI needs to read the runtime mode from the manifest
- When deploying async functions, it should:
  - Set appropriate environment variables
  - Pass the `--asgi` flag to functions-framework
  - Potentially use different container configurations

### Phase 4: Testing and Validation

#### 4.1 Test Coverage
- Add async versions of existing tests
- Test mixed deployments (both sync and async functions)
- Verify proper error handling in async contexts
- Test timeout behavior for async functions

#### 4.2 Example Updates
- Update examples to show async usage
- Create migration guide for converting sync to async

## Example Usage

### HTTP Functions
```python
from firebase_functions import https_fn
from firebase_functions.aio import https_fn as async_https_fn

# Sync (existing)
@https_fn.on_request()
def sync_http(request: Request) -> Response:
    return Response("Hello sync")

# Async (new)
@async_https_fn.on_request()
async def async_http(request) -> Response:  # Will be Starlette Request
    result = await some_async_api_call()
    return Response(f"Hello async: {result}")

# Sync function in aio namespace (also supported)
@async_https_fn.on_request()
def sync_in_async_http(request) -> Response:
    # This sync function will run in ASGI's thread pool
    return Response("Hello from sync in async")
```

### Firestore Functions
```python
# Sync (existing)
@firestore_fn.on_document_created(document="users/{userId}")
def sync_user_created(event: Event[DocumentSnapshot]) -> None:
    print(f"User created: {event.data.id}")

# Async (new)
@firestore_fn.on_document_created(document="users/{userId}")
async def async_user_created(event: Event[DocumentSnapshot]) -> None:
    await send_welcome_email(event.data.get("email"))
    await update_analytics(event.data.id)
```

### Pub/Sub Functions
```python
# Async (new)
@pubsub_fn.on_message_published(topic="process-queue")
async def async_process_message(event: CloudEvent[MessagePublishedData]) -> None:
    message = event.data.message
    await process_job(message.data)
```

## Benefits

1. **Performance**: Async functions can handle I/O-bound operations more efficiently
2. **Scalability**: Better resource utilization for functions that make external API calls
3. **Modern Python**: Aligns with Python's async/await ecosystem
4. **Flexibility**: Users can choose sync or async based on their needs

## Considerations

1. **Cold Start**: Need to verify async functions don't increase cold start times
2. **Memory Usage**: Monitor if async runtime uses more memory
3. **Debugging**: Ensure stack traces and error messages are clear for async functions
4. **Timeouts**: Verify timeout behavior works correctly with async functions

## Migration Path

1. Start with HTTP functions as proof of concept
2. Extend to event-triggered functions
3. Update documentation and examples
4. Release as minor version update (backward compatible)

## Implementation Status

### Completed (Phase 1)
- ✅ HTTP functions (on_request and on_call) with async support
- ✅ Shared business logic to avoid code duplication
- ✅ CORS handling for async functions
- ✅ Type safety with overloads
- ✅ Support for both sync and async functions in aio namespace
- ✅ Comprehensive tests

### Remaining Work
- Event-triggered functions (Firestore, Database, Storage, etc.)
- Documentation and examples
- Integration with Firebase CLI for deployment

## Open Questions

1. Should we support both Flask and Starlette response types for async HTTP functions?
2. How should we handle async context managers and cleanup?
3. Should we provide async versions of Firebase Admin SDK operations?

## Next Steps

1. Prototype async support for HTTP functions
2. Test with functions-framework in ASGI mode
3. Design type system for handling both sync and async
4. Update manifest generation
5. Coordinate with Firebase CLI team for deployment support