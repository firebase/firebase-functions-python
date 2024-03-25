import json
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

mocked_modules = {
    "google.cloud.firestore": MagicMock(),
    "google.cloud.firestore_v1": MagicMock(),
    "firebase_admin": MagicMock()
}


class TestFirestore(TestCase):
    def test_firestore_endpoint_handler_calls_function_with_correct_args(self):
        with patch.dict('sys.modules', mocked_modules):
            from cloudevents.http import CloudEvent
            from firebase_functions import firestore_fn
            from firebase_functions.private import path_pattern

            func = Mock(__name__="example_func")

            event_type = firestore_fn._event_type_created_with_auth_context
            document_pattern = path_pattern.PathPattern("foo/{bar}")
            raw_event = CloudEvent(
                attributes={
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
                    "authid": "foo"
                },
                data=json.dumps({})
            )

            firestore_fn._firestore_endpoint_handler(func=func,
                                                     event_type=event_type,
                                                     document_pattern=document_pattern,
                                                     raw=raw_event)

            func.assert_called_once()

            event = func.call_args.args[0]
            self.assertIsNotNone(event)
            self.assertIsInstance(event, firestore_fn.EventWithAuthContext)
            self.assertEqual(event.auth_type, "unauthenticated")
            self.assertEqual(event.auth_id, "foo")
