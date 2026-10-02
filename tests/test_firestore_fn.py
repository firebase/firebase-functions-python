"""
This module contains tests for the firestore_fn module.
"""

import json
import os
import threading
import time
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch


class TestFirestore(TestCase):
    """
    firestore_fn tests.
    """

    def setUp(self):
        from firebase_functions import firestore_fn

        firestore_fn._firestore_clients.clear()

    def _create_event(self, project: str = "project-id", database: str = "(default)"):
        from cloudevents.http import CloudEvent

        from firebase_functions import firestore_fn

        attributes = {
            "specversion": "1.0",
            "type": firestore_fn._event_type_created,
            "source": "https://example.com/testevent",
            "time": "2023-03-11T13:25:37.403Z",
            "subject": "test_subject",
            "datacontenttype": "application/json",
            "location": f"projects/{project}/databases/{database}/documents/foo/bar",
            "project": project,
            "namespace": "(default)",
            "document": "foo/bar",
            "database": database,
            "authtype": "unauthenticated",
            "authid": "foo",
        }
        return CloudEvent(attributes=attributes, data=json.dumps({}))

    def test_firestore_endpoint_handler_calls_function_with_correct_args(self):
        from cloudevents.http import CloudEvent

        from firebase_functions.firestore_fn import (
            AuthEvent,
        )
        from firebase_functions.firestore_fn import (
            _event_type_created_with_auth_context as event_type,
        )
        from firebase_functions.firestore_fn import (
            _firestore_endpoint_handler as firestore_endpoint_handler,
        )
        from firebase_functions.private import path_pattern

        func = Mock(__name__="example_func")
        document_pattern = path_pattern.PathPattern("foo/{bar}")
        attributes = {
            "specversion": "1.0",
            "type": event_type,
            "source": "https://example.com/testevent",
            "time": "2023-03-11T13:25:37.403Z",
            "subject": "test_subject",
            "datacontenttype": "application/json",
            "location": "projects/project-id/databases/(default)/documents/foo/{bar}",
            "project": "project-id",
            "namespace": "(default)",
            "document": "foo/{bar}",
            "database": "(default)",
            "authtype": "unauthenticated",
            "authid": "foo",
        }
        raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client"),
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            firestore_endpoint_handler(
                func=func, event_type=event_type, document_pattern=document_pattern, raw=raw_event
            )

        func.assert_called_once()

        event = func.call_args.args[0]
        self.assertIsNotNone(event)
        self.assertIsInstance(event, AuthEvent)
        self.assertEqual(event.auth_type, "unauthenticated")
        self.assertEqual(event.auth_id, "foo")

    def test_calls_init_function(self):
        from cloudevents.http import CloudEvent

        from firebase_functions import core, firestore_fn

        func = Mock(__name__="example_func")
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        attributes = {
            "specversion": "1.0",
            "type": firestore_fn._event_type_created,
            "source": "https://example.com/testevent",
            "time": "2023-03-11T13:25:37.403Z",
            "subject": "test_subject",
            "datacontenttype": "application/json",
            "location": "projects/project-id/databases/(default)/documents/foo/{bar}",
            "project": "project-id",
            "namespace": "(default)",
            "document": "foo/{bar}",
            "database": "(default)",
            "authtype": "unauthenticated",
            "authid": "foo",
        }
        raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client"),
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)
            decorated_func(raw_event)

        self.assertEqual(hello, "world")

    @patch.dict(os.environ, {}, clear=False)
    def test_firestore_client_is_cached(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        from firebase_functions import firestore_fn

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client") as mock_client_cls,
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            func = Mock(__name__="example_func")
            raw_event = self._create_event()
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            decorated_func(raw_event)
            decorated_func(raw_event)

            self.assertEqual(mock_client_cls.call_count, 1)
            mock_client_cls.assert_called_once_with(
                project="project-id",
                database="(default)",
                credentials=app.credential.get_credential(),
            )
            self.assertIn(
                ("project-id", "(default)", None, app.credential),
                firestore_fn._firestore_clients,
            )

    @patch.dict(os.environ, {}, clear=False)
    def test_firestore_client_is_cached_concurrent(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        from firebase_functions import firestore_fn

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client") as mock_client_cls,
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            func = Mock(__name__="example_func")
            raw_event = self._create_event()
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            t1_can_proceed = threading.Event()
            t2_can_proceed = threading.Event()

            self.addCleanup(t1_can_proceed.set)
            self.addCleanup(t2_can_proceed.set)

            call_count = 0

            def mock_client_init(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    t1_can_proceed.set()
                    t2_can_proceed.wait(timeout=5)
                return MagicMock()

            mock_client_cls.side_effect = mock_client_init
            self.addCleanup(lambda: setattr(mock_client_cls, "side_effect", None))

            def run_func():
                decorated_func(raw_event)

            t1 = threading.Thread(target=run_func)
            t1.start()

            t1_can_proceed.wait(timeout=5)

            t2 = threading.Thread(target=run_func)
            t2.start()

            # Ensure t2 actually contends on the lock while t1 is inside mock_client_init
            time.sleep(0.1)
            t2_can_proceed.set()

            t1.join(timeout=5)
            t2.join(timeout=5)

            self.assertEqual(mock_client_cls.call_count, 1)
            self.assertIn(
                ("project-id", "(default)", None, app.credential),
                firestore_fn._firestore_clients,
            )

    @patch.dict(os.environ, {}, clear=False)
    def test_firestore_client_cache_isolation(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        from firebase_functions import firestore_fn

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client") as mock_client_cls,
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.credential = MagicMock()
            mock_get_app.return_value = app

            func = Mock(__name__="example_func")
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            # Project A, Database (default)
            app.project_id = "project-A"
            decorated_func(self._create_event("project-A", "(default)"))

            # Project A, Database (default) -> Cached
            decorated_func(self._create_event("project-A", "(default)"))

            # Project B, Database (default) -> New client
            app.project_id = "project-B"
            decorated_func(self._create_event("project-B", "(default)"))

            # Project A, Database other -> New client
            app.project_id = "project-A"
            decorated_func(self._create_event("project-A", "other"))

            self.assertEqual(mock_client_cls.call_count, 3)

    @patch.dict(os.environ, {}, clear=False)
    def test_firestore_client_creation_failure_does_not_poison_cache(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        from firebase_functions import firestore_fn

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client") as mock_client_cls,
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            func = Mock(__name__="example_func")
            raw_event = self._create_event(project="project-id", database="(default)")
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            class InitializationError(Exception):
                pass

            mock_client_cls.side_effect = InitializationError("Initialization failed")
            self.addCleanup(lambda: setattr(mock_client_cls, "side_effect", None))

            with self.assertRaisesRegex(InitializationError, "Initialization failed"):
                decorated_func(raw_event)

            self.assertNotIn(
                ("project-id", "(default)", None, app.credential),
                firestore_fn._firestore_clients,
            )

            mock_client_cls.side_effect = None
            decorated_func(raw_event)

            self.assertIn(
                ("project-id", "(default)", None, app.credential),
                firestore_fn._firestore_clients,
            )

    @patch.dict(os.environ, {"FIRESTORE_EMULATOR_HOST": "localhost:8080"}, clear=False)
    def test_firestore_client_emulator_skips_credentials(self):
        from firebase_functions import firestore_fn

        with (
            patch("firebase_functions.firestore_fn._firestore_v1.Client") as mock_client_cls,
            patch("firebase_functions.firestore_fn.get_app") as mock_get_app,
        ):
            app = MagicMock()
            app.options = {}
            app.project_id = "project-id"
            app.credential = MagicMock()
            mock_get_app.return_value = app

            func = Mock(__name__="example_func")
            raw_event = self._create_event()
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            decorated_func(raw_event)
            decorated_func(raw_event)

            self.assertEqual(mock_client_cls.call_count, 1)
            mock_client_cls.assert_called_with(
                project="project-id",
                database="(default)",
            )
            app.credential.get_credential.assert_not_called()
