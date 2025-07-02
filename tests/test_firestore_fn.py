"""
This module contains tests for the firestore_fn module.
"""

import json
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
