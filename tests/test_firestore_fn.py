"""
This module contains tests for the firestore_fn module.
"""

import json
import os
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

mocked_modules = {
    "google.cloud.firestore": MagicMock(),
    "google.cloud.firestore_v1": MagicMock(),
    "firebase_admin": MagicMock(),
}


class TestFirestore(TestCase):
    """
    firestore_fn tests.
    """

    def test_firestore_endpoint_handler_calls_function_with_correct_args(self):
        with patch.dict("sys.modules", mocked_modules):
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
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))

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
        with patch.dict("sys.modules", mocked_modules):
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
                # pylint: disable=protected-access
                "type": firestore_fn._event_type_created,
                "source": "https://example.com/testevent",
                "time": "2023-03-11T13:25:37.403Z",
                "subject": "test_subject",
                "datacontenttype": "application/json",
                "location": "projects/project-id/databases/(default)/documents/foo/{bar}",
                "project": "project-id",
                "namespace": "(default)",
                "document": "foo/{bar}",
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            decorated_func(raw_event)

            self.assertEqual(hello, "world")

    @patch.dict(os.environ, clear=False)
    def test_firestore_client_is_cached(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        with patch.dict("sys.modules", mocked_modules):
            from cloudevents.http import CloudEvent

            from firebase_functions import firestore_fn

            firestore_fn._firestore_clients.clear()

            func = Mock(__name__="example_func")
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
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            mock_client_cls = mocked_modules["google.cloud.firestore_v1"].Client
            mock_client_cls.reset_mock()

            decorated_func(raw_event)
            decorated_func(raw_event)
            decorated_func(raw_event)

            self.assertEqual(mock_client_cls.call_count, 1)
            mock_client_cls.assert_called_with(
                project=mocked_modules["firebase_admin"].get_app().project_id,
                database="projects/project-id/databases/(default)",
                credentials=mocked_modules["firebase_admin"].get_app().credential.get_credential(),
            )

    @patch.dict(os.environ, clear=False)
    def test_firestore_client_is_cached_concurrent(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        with patch.dict("sys.modules", mocked_modules):
            import threading

            from cloudevents.http import CloudEvent

            from firebase_functions import firestore_fn

            firestore_fn._firestore_clients.clear()

            func = Mock(__name__="example_func")
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
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            mock_client_cls = mocked_modules["google.cloud.firestore_v1"].Client
            mock_client_cls.reset_mock()

            app = mocked_modules["firebase_admin"].get_app()
            get_cred_mock = app.credential.get_credential
            get_cred_mock.reset_mock()

            t1_in_critical_section = threading.Event()
            t1_can_proceed = threading.Event()

            t2_in_critical_section = threading.Event()
            t2_can_proceed = threading.Event()

            def get_credential_side_effect(*args, **kwargs):
                if not t1_in_critical_section.is_set():
                    t1_in_critical_section.set()
                    t1_can_proceed.wait()
                else:
                    t2_in_critical_section.set()
                    t2_can_proceed.wait()
                return "mock_cred"

            get_cred_mock.side_effect = get_credential_side_effect

            def thread_task():
                decorated_func(raw_event)

            t1 = threading.Thread(target=thread_task)
            t2 = threading.Thread(target=thread_task)

            t1.start()
            self.assertTrue(
                t1_in_critical_section.wait(timeout=5.0),
                "Thread 1 failed to reach the critical section",
            )

            t2.start()
            raced = t2_in_critical_section.wait(timeout=0.5)

            t1_can_proceed.set()
            t1.join()

            t2_can_proceed.set()
            t2.join()

            get_cred_mock.side_effect = None

            self.assertFalse(
                raced,
                "Race condition detected! Multiple threads entered initialization simultaneously.",
            )
            self.assertEqual(mock_client_cls.call_count, 1)

    @patch.dict(os.environ, clear=False)
    def test_firestore_client_cache_isolation(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        with patch.dict("sys.modules", mocked_modules):
            from cloudevents.http import CloudEvent

            from firebase_functions import firestore_fn

            firestore_fn._firestore_clients.clear()

            func = Mock(__name__="example_func")

            def create_event(project: str, database: str):
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
                    "database": f"projects/{project}/databases/{database}",
                    "authtype": "unauthenticated",
                    "authid": "foo",
                }
                return CloudEvent(attributes=attributes, data=json.dumps({}))

            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            mock_client_cls = mocked_modules["google.cloud.firestore_v1"].Client
            mock_client_cls.reset_mock()

            app = mocked_modules["firebase_admin"].get_app()
            original_project_id = app.project_id
            self.addCleanup(lambda: setattr(app, "project_id", original_project_id))

            # Project A, Database (default)
            app.project_id = "project-A"
            decorated_func(create_event("project-A", "(default)"))

            # Project A, Database (default) -> Cached
            decorated_func(create_event("project-A", "(default)"))

            # Project B, Database (default) -> New client
            app.project_id = "project-B"
            decorated_func(create_event("project-B", "(default)"))

            # Project A, Database other -> New client
            app.project_id = "project-A"
            decorated_func(create_event("project-A", "other"))

            self.assertEqual(mock_client_cls.call_count, 3)

    @patch.dict(os.environ, clear=False)
    def test_firestore_client_creation_failure_does_not_poison_cache(self):
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        with patch.dict("sys.modules", mocked_modules):
            from cloudevents.http import CloudEvent

            from firebase_functions import firestore_fn

            firestore_fn._firestore_clients.clear()

            func = Mock(__name__="example_func")
            attributes = {
                "specversion": "1.0",
                "type": firestore_fn._event_type_created,
                "source": "https://example.com/testevent",
                "time": "2023-03-11T13:25:37.403Z",
                "subject": "test_subject",
                "datacontenttype": "application/json",
                "location": "projects/project-id/databases/(default)/documents/foo/bar",
                "project": "project-id",
                "namespace": "(default)",
                "document": "foo/bar",
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            mock_client_cls = mocked_modules["google.cloud.firestore_v1"].Client
            app = mocked_modules["firebase_admin"].get_app()
            app.project_id = "project-id"

            class InitializationError(Exception):
                pass

            mock_client_cls.side_effect = InitializationError("Initialization failed")
            self.addCleanup(lambda: setattr(mock_client_cls, "side_effect", None))

            with self.assertRaises(InitializationError):
                decorated_func(raw_event)

            self.assertNotIn(
                ("project-id", "projects/project-id/databases/(default)"),
                firestore_fn._firestore_clients,
            )

            mock_client_cls.side_effect = None
            mock_client_cls.return_value = MagicMock()

            decorated_func(raw_event)

            self.assertIn(
                ("project-id", "projects/project-id/databases/(default)"),
                firestore_fn._firestore_clients,
            )

    @patch.dict("os.environ", {"FIRESTORE_EMULATOR_HOST": "localhost:8080"})
    def test_firestore_client_emulator_skips_credentials(self):
        with patch.dict("sys.modules", mocked_modules):
            from cloudevents.http import CloudEvent

            from firebase_functions import firestore_fn

            firestore_fn._firestore_clients.clear()

            func = Mock(__name__="example_func")
            attributes = {
                "specversion": "1.0",
                "type": firestore_fn._event_type_created,
                "source": "https://example.com/testevent",
                "time": "2023-03-11T13:25:37.403Z",
                "subject": "test_subject",
                "datacontenttype": "application/json",
                "location": "projects/project-id/databases/(default)/documents/foo/bar",
                "project": "project-id",
                "namespace": "(default)",
                "document": "foo/bar",
                "database": "projects/project-id/databases/(default)",
                "authtype": "unauthenticated",
                "authid": "foo",
            }
            raw_event = CloudEvent(attributes=attributes, data=json.dumps({}))
            decorated_func = firestore_fn.on_document_created(document="/foo/{bar}")(func)

            mock_client_cls = mocked_modules["google.cloud.firestore_v1"].Client
            mock_client_cls.reset_mock()
            app = mocked_modules["firebase_admin"].get_app()
            app.credential.get_credential.reset_mock()

            decorated_func(raw_event)

            self.assertEqual(mock_client_cls.call_count, 1)
            mock_client_cls.assert_called_with(
                project=app.project_id,
                database="projects/project-id/databases/(default)",
            )
            app.credential.get_credential.assert_not_called()
