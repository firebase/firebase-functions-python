# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Internal utils tests.
"""

import datetime as _dt
from os import environ, path

from firebase_functions.private.util import (
    _unsafe_decode_id_token,
    deep_merge,
    firebase_config,
    normalize_path,
    timestamp_conversion,
)

test_bucket = "python-functions-testing.appspot.com"
test_config_file = path.join(path.dirname(path.realpath(__file__)), "firebase_config_test.json")


def test_firebase_config_loads_from_env_json():
    """
    Testing firebase_config can be read from the
    FIREBASE_CONFIG env var as a JSON string.
    """
    environ["FIREBASE_CONFIG"] = f'{{"storageBucket": "{test_bucket}"}}'
    assert firebase_config().storage_bucket == test_bucket, (
        "Failure, firebase_config did not load from env variable."
    )


def test_firebase_config_loads_from_env_file():
    """
    Testing firebase_config can be read from the
    FIREBASE_CONFIG env var as a file path.
    """
    environ["FIREBASE_CONFIG"] = test_config_file
    assert firebase_config().storage_bucket == test_bucket, (
        "Failure, firebase_config did not load from env variable."
    )


def test_timestamp_conversion_supported_formats():
    """
    Testing shared timestamp conversion handles supported RTDB and CloudEvent formats.
    """
    timestamps = [
        (
            "2024-04-10T12:00:00.000Z",
            _dt.datetime(2024, 4, 10, 12, 0, tzinfo=_dt.timezone.utc),
        ),
        (
            "2024-04-10T12:00:00.123456Z",
            _dt.datetime(2024, 4, 10, 12, 0, 0, 123456, tzinfo=_dt.timezone.utc),
        ),
        (
            "2024-04-10T12:00:00.123456+05:30",
            _dt.datetime(
                2024,
                4,
                10,
                12,
                0,
                0,
                123456,
                tzinfo=_dt.timezone(_dt.timedelta(hours=5, minutes=30)),
            ),
        ),
        (
            "2024-04-10T12:00:00.123456-0700",
            _dt.datetime(
                2024,
                4,
                10,
                12,
                0,
                0,
                123456,
                tzinfo=_dt.timezone(-_dt.timedelta(hours=7)),
            ),
        ),
        (
            "2023-01-01T12:34:56.123456789Z",
            _dt.datetime(2023, 1, 1, 12, 34, 56, 123456, tzinfo=_dt.timezone.utc),
        ),
        (
            "2023-01-01T12:34:56.123456789+05:30",
            _dt.datetime(
                2023,
                1,
                1,
                12,
                34,
                56,
                123456,
                tzinfo=_dt.timezone(_dt.timedelta(hours=5, minutes=30)),
            ),
        ),
        (
            "2025-10-30T21:15:51Z",
            _dt.datetime(2025, 10, 30, 21, 15, 51, tzinfo=_dt.timezone.utc),
        ),
    ]

    for input_timestamp, expected_datetime in timestamps:
        assert timestamp_conversion(input_timestamp) == expected_datetime


def test_normalize_document_path():
    """
    Testing "document" path passed to Firestore event listener
    is normalized.
    """
    test_path = "/test/document/"
    assert normalize_path(test_path) == "test/document", "Failure, path was not normalized."

    test_path1 = "//////test/document//////////"
    assert normalize_path(test_path1) == "test/document", "Failure, path was not normalized."

    test_path2 = "test/document"
    assert normalize_path(test_path2) == "test/document", (
        "Failure, path should not be changed if it is already normalized."
    )


def test_toplevel_keys():
    dict1 = {"baz": {"answer": 42, "qux": "quux"}, "foo": "bar"}
    dict2 = {"baz": {"answer": 33}}
    result = deep_merge(dict1, dict2)
    assert "foo" in result
    assert "baz" in result


def test_nested_merge():
    dict1 = {"baz": {"answer": 42, "qux": "quux"}, "foo": "bar"}
    dict2 = {"baz": {"answer": 33}}
    result = deep_merge(dict1, dict2)
    assert result["baz"]["answer"] == 33
    assert result["baz"]["qux"] == "quux"


def test_does_not_modify_originals():
    dict1 = {"baz": {"answer": 42, "qux": "quux"}, "foo": "bar"}
    dict2 = {"baz": {"answer": 33}}
    deep_merge(dict1, dict2)
    assert dict1["baz"]["answer"] == 42
    assert dict2["baz"]["answer"] == 33


def test_unsafe_decode_token():
    # pylint: disable=line-too-long
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaXJlYmFzZSIsIm5hbWUiOiJKb2huIERvZSJ9.74A24Y821E7CZx8aYCsCKo0Y-W0qXwqME-14QlEMcB0"
    result = _unsafe_decode_id_token(test_token)
    assert result["sub"] == "firebase"
    assert result["name"] == "John Doe"
