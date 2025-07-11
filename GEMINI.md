# GEMINI.md

This file provides guidance to coding agents when working with code in this repository.

## Project Overview

Firebase Functions Python SDK - A Python SDK for defining Firebase Functions that respond to Firebase and Google Cloud events using decorators or HTTP requests.

## Development Commands

All commands use the Makefile:

- `make install` - Install dependencies with uv
- `make lint` - Run ruff linter
- `make format` - Format code with ruff
- `make format-check` - Check formatting without modifying
- `make typecheck` - Run type checking with mypy
- `make test` - Run tests
- `make test-cov` - Run tests with coverage report
- `make docs` - Generate documentation

### Testing Individual Functions

```bash
# Run specific test file
uv run pytest tests/test_https_fn.py

# Run specific test
uv run pytest tests/test_https_fn.py::test_on_request_no_args

# Run with verbose output
uv run pytest -vv tests/test_firestore_fn.py
```

## Architecture

### Core Design Pattern

The SDK uses a decorator-based API where functions are defined using specific decorators for different trigger types:

```python
@https_fn.on_request()
@firestore_fn.on_document_created(document="posts/{postId}")
@pubsub_fn.on_message_published(topic="my-topic")
```

### Key Components

1. **Function Modules** (`src/firebase_functions/`):
   - Each trigger type has its own module (e.g., `https_fn.py`, `firestore_fn.py`)
   - All decorators follow a similar pattern: validate options → create endpoint metadata → wrap function

2. **Core Infrastructure** (`src/firebase_functions/core.py`):
   - `CloudEvent` and `Event` classes for event data
   - Endpoint metadata stored in `__firebase_endpoint__` attribute
   - Type definitions for various event types

3. **Private Modules** (`src/firebase_functions/private/`):
   - `manifest.py` - Generates deployment manifests
   - `serving.py` - Handles function serving and registration
   - `util.py` - Common utilities

4. **Options Pattern**:
   - Each function type has an options dataclass (e.g., `HttpsOptions`, `FirestoreOptions`)
   - Options control deployment settings like memory, timeout, regions, etc.

### Function Registration Flow

1. Decorator validates options and creates `ManifestEndpoint`
2. Endpoint metadata attached to function via `__firebase_endpoint__`
3. During deployment, `manifest.py` collects all decorated functions
4. Functions registered with `functions-framework` for runtime handling

## Testing Strategy

- Each function type has comprehensive tests in `/tests/`
- Tests use `unittest.mock` for mocking Firebase services
- Don't overuse mocks
- Test both successful cases and error conditions
- Verify endpoint metadata is correctly set

## Code Quality Requirements

Before committing changes:

1. Run `make lint` and fix any issues
2. Run `make typecheck` and fix type errors
3. Run `make format` to ensure consistent formatting
4. Run `make test` to ensure all tests pass
5. Add tests for new functionality

## Important Notes

- Python 3.10+ required
- Uses `uv` package manager (not pip/poetry)
- Built on top of Google's `functions-framework`
- All public APIs should maintain backward compatibility
- Follow existing patterns when adding new trigger types

