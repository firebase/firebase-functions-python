"""
Tests for the dataconnect_fn module.
"""

import json
import unittest
from unittest import mock

from cloudevents.http import CloudEvent

from firebase_functions import core, dataconnect_fn


class TestDataConnect(unittest.TestCase):
    """
    Tests for the dataconnect_fn module.
    """

    def test_on_mutation_executed_decorator(self):
        """
        Tests on_mutation_executed decorator functionality by checking that the
        __firebase_endpoint__ attribute is set properly.
        """
        func = mock.Mock(__name__="example_func")
        decorated_func = dataconnect_fn.on_mutation_executed(
            service="service-id",
            connector="connector-id",
            operation="mutation-name",
        )(func)
        endpoint = decorated_func.__firebase_endpoint__
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertEqual(
            endpoint.eventTrigger["eventType"],
            "google.firebase.dataconnect.connector.v1.mutationExecuted",
        )
        self.assertIsNotNone(endpoint.eventTrigger["eventFilters"])
        self.assertEqual(endpoint.eventTrigger["eventFilters"]["service"], "service-id")
        self.assertEqual(endpoint.eventTrigger["eventFilters"]["connector"], "connector-id")
        self.assertEqual(endpoint.eventTrigger["eventFilters"]["operation"], "mutation-name")

    def test_on_mutation_executed_decorator_optional_filters(self):
        """
        Tests on_mutation_executed decorator functionality by checking that the
        __firebase_endpoint__ attribute is set properly.
        """
        func = mock.Mock(__name__="example_func")
        decorated_func = dataconnect_fn.on_mutation_executed()(func)
        endpoint = decorated_func.__firebase_endpoint__
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertEqual(
            endpoint.eventTrigger["eventType"],
            "google.firebase.dataconnect.connector.v1.mutationExecuted",
        )
        self.assertIsNotNone(endpoint.eventTrigger["eventFilters"])
        self.assertEqual(endpoint.eventTrigger["eventFilters"], {})

    def test_on_mutation_executed_decorator_with_captures(self):
        """
        Tests on_mutation_executed decorator functionality by checking that the
        __firebase_endpoint__ attribute is set properly.

        Tests that captures are handled correctly.
        """
        func = mock.Mock(__name__="example_func")
        decorated_func = dataconnect_fn.on_mutation_executed(
            service="{service}",
            connector="{connector}",
            operation="{operation}",
        )(func)
        endpoint = decorated_func.__firebase_endpoint__
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertEqual(
            endpoint.eventTrigger["eventType"],
            "google.firebase.dataconnect.connector.v1.mutationExecuted",
        )
        self.assertIsNotNone(endpoint.eventTrigger["eventFilterPathPatterns"])
        self.assertEqual(endpoint.eventTrigger["eventFilterPathPatterns"]["service"], "{service}")
        self.assertEqual(
            endpoint.eventTrigger["eventFilterPathPatterns"]["connector"], "{connector}"
        )
        self.assertEqual(
            endpoint.eventTrigger["eventFilterPathPatterns"]["operation"], "{operation}"
        )

    def test_on_mutation_executed_decorator_with_wildcards(self):
        """
        Tests on_mutation_executed decorator functionality by checking that the
        __firebase_endpoint__ attribute is set properly.

        Tests that captures are handled correctly.
        """
        func = mock.Mock(__name__="example_func")
        decorated_func = dataconnect_fn.on_mutation_executed(
            service="*",
            connector="*",
            operation="*",
        )(func)
        endpoint = decorated_func.__firebase_endpoint__
        self.assertIsNotNone(endpoint)
        self.assertIsNotNone(endpoint.eventTrigger)
        self.assertEqual(
            endpoint.eventTrigger["eventType"],
            "google.firebase.dataconnect.connector.v1.mutationExecuted",
        )
        self.assertIsNotNone(endpoint.eventTrigger["eventFilterPathPatterns"])
        self.assertEqual(endpoint.eventTrigger["eventFilterPathPatterns"]["service"], "*")
        self.assertEqual(endpoint.eventTrigger["eventFilterPathPatterns"]["connector"], "*")
        self.assertEqual(endpoint.eventTrigger["eventFilterPathPatterns"]["operation"], "*")

    def test_calls_init_function(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        event = CloudEvent(
            attributes={
                "specversion": "1.0",
                "id": "id",
                "type": "google.firebase.dataconnect.connector.v1.mutationExecuted",
                "source": "source",
                "subject": "subject",
                "time": "2024-04-10T12:00:00.000Z",
                "project": "project-id",
                "location": "location-id",
                "service": "service-id",
                "connector": "connector-id",
                "operation": "mutation-name",
                "authtype": "app_user",
                "authid": "auth-id",
            },
            data=json.dumps({}),
        )

        func = mock.Mock(__name__="example_func")
        decorated_func = dataconnect_fn.on_mutation_executed(
            service="service-id", connector="connector-id", operation="mutation-name"
        )(func)
        decorated_func(event)

        func.assert_called_once()
        event = func.call_args.args[0]
        self.assertIsNotNone(event)
        self.assertEqual(event.project, "project-id")
        self.assertEqual(event.location, "location-id")
        self.assertEqual(event.auth_type, "app_user")
        self.assertEqual(event.auth_id, "auth-id")

        self.assertEqual(hello, "world")
