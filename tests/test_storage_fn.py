"""
Tests for the storage function.
"""

import unittest
from unittest.mock import Mock

from cloudevents.http import CloudEvent

from firebase_functions import core, storage_fn


class TestStorage(unittest.TestCase):
    """
    Storage function tests.
    """

    def test_calls_init(self):
        hello = None

        @core.init
        def init():
            nonlocal hello
            hello = "world"

        func = Mock(__name__="example_func")
        event = CloudEvent(
            attributes={"source": "source", "type": "type"},
            data={
                "bucket": "bucket",
                "generation": "generation",
                "id": "id",
                "metageneration": "metageneration",
                "name": "name",
                "size": "size",
                "storageClass": "storageClass",
            },
        )

        decorated_func = storage_fn.on_object_archived(bucket="bucket")(func)
        decorated_func(event)

        self.assertEqual("world", hello)
