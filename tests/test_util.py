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
from os import environ, path
from firebase_functions.private.util import firebase_config, microsecond_timestamp_conversion, nanoseconds_timestamp_conversion, get_precision_timestamp, normalize_path, deep_merge, PrecisionTimestamp, second_timestamp_conversion
import datetime as _dt

test_bucket = "python-functions-testing.appspot.com"
test_config_file = path.join(path.dirname(path.realpath(__file__)),
                             "firebase_config_test.json")


def test_firebase_config_loads_from_env_json():
    """
    Testing firebase_config can be read from the
    FIREBASE_CONFIG env var as a JSON string.
    """
    environ["FIREBASE_CONFIG"] = f'{{"storageBucket": "{test_bucket}"}}'
    assert firebase_config().storage_bucket == test_bucket, (
        "Failure, firebase_config did not load from env variable.")


def test_firebase_config_loads_from_env_file():
    """
    Testing firebase_config can be read from the
    FIREBASE_CONFIG env var as a file path.
    """
    environ["FIREBASE_CONFIG"] = test_config_file
    assert firebase_config().storage_bucket == test_bucket, (
        "Failure, firebase_config did not load from env variable.")


def test_microsecond_conversion():
    """
    Testing microsecond_timestamp_conversion works as intended
    """
    timestamps = [
        ("2023-06-20T10:15:22.396358Z", "2023-06-20T10:15:22.396358Z"),
        ("2021-02-20T11:23:45.987123Z", "2021-02-20T11:23:45.987123Z"),
        ("2022-09-18T09:15:38.246824Z", "2022-09-18T09:15:38.246824Z"),
        ("2010-09-18T09:15:38.246824Z", "2010-09-18T09:15:38.246824Z"),
    ]

    for input_timestamp, expected_output in timestamps:
        expected_datetime = _dt.datetime.strptime(expected_output,
                                                  "%Y-%m-%dT%H:%M:%S.%fZ")
        expected_datetime = expected_datetime.replace(tzinfo=_dt.timezone.utc)
        assert microsecond_timestamp_conversion(
            input_timestamp) == expected_datetime


def test_nanosecond_conversion():
    """
    Testing nanoseconds_timestamp_conversion works as intended
    """
    timestamps = [
        ("2023-01-01T12:34:56.123456789Z", "2023-01-01T12:34:56.123456Z"),
        ("2023-02-14T14:37:52.987654321Z", "2023-02-14T14:37:52.987654Z"),
        ("2023-03-21T06:43:58.564738291Z", "2023-03-21T06:43:58.564738Z"),
        ("2023-08-15T22:22:22.222222222Z", "2023-08-15T22:22:22.222222Z"),
    ]

    for input_timestamp, expected_output in timestamps:
        expected_datetime = _dt.datetime.strptime(expected_output,
                                                  "%Y-%m-%dT%H:%M:%S.%fZ")
        expected_datetime = expected_datetime.replace(tzinfo=_dt.timezone.utc)
        assert nanoseconds_timestamp_conversion(
            input_timestamp) == expected_datetime


def test_second_conversion():
    """
    Testing seconds_timestamp_conversion works as intended
    """
    timestamps = [
        ("2023-01-01T12:34:56Z", "2023-01-01T12:34:56Z"),
        ("2023-02-14T14:37:52Z", "2023-02-14T14:37:52Z"),
        ("2023-03-21T06:43:58Z", "2023-03-21T06:43:58Z"),
        ("2023-10-06T07:00:00Z", "2023-10-06T07:00:00Z"),
    ]

    for input_timestamp, expected_output in timestamps:
        expected_datetime = _dt.datetime.strptime(expected_output,
                                                  "%Y-%m-%dT%H:%M:%SZ")
        expected_datetime = expected_datetime.replace(tzinfo=_dt.timezone.utc)
        assert second_timestamp_conversion(input_timestamp) == expected_datetime


def test_is_nanoseconds_timestamp():
    """
    Testing is_nanoseconds_timestamp works as intended
    """
    microsecond_timestamp1 = "2023-06-20T10:15:22.396358Z"
    microsecond_timestamp2 = "2021-02-20T11:23:45.987123Z"
    microsecond_timestamp3 = "2022-09-18T09:15:38.246824Z"
    microsecond_timestamp4 = "2010-09-18T09:15:38.246824Z"

    nanosecond_timestamp1 = "2023-01-01T12:34:56.123456789Z"
    nanosecond_timestamp2 = "2023-02-14T14:37:52.987654321Z"
    nanosecond_timestamp3 = "2023-03-21T06:43:58.564738291Z"
    nanosecond_timestamp4 = "2023-08-15T22:22:22.222222222Z"

    second_timestamp1 = "2023-01-01T12:34:56Z"
    second_timestamp2 = "2023-02-14T14:37:52Z"
    second_timestamp3 = "2023-03-21T06:43:58Z"
    second_timestamp4 = "2023-08-15T22:22:22Z"

    assert get_precision_timestamp(
        microsecond_timestamp1) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(
        microsecond_timestamp2) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(
        microsecond_timestamp3) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(
        microsecond_timestamp4) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(
        nanosecond_timestamp1) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(
        nanosecond_timestamp2) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(
        nanosecond_timestamp3) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(
        nanosecond_timestamp4) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(
        second_timestamp1) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(
        second_timestamp2) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(
        second_timestamp3) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(
        second_timestamp4) is PrecisionTimestamp.SECONDS


def test_normalize_document_path():
    """
    Testing "document" path passed to Firestore event listener
    is normalized.
    """
    test_path = "/test/document/"
    assert normalize_path(test_path) == "test/document", (
        "Failure, path was not normalized.")

    test_path1 = "//////test/document//////////"
    assert normalize_path(test_path1) == "test/document", (
        "Failure, path was not normalized.")

    test_path2 = "test/document"
    assert normalize_path(test_path2) == "test/document", (
        "Failure, path should not be changed if it is already normalized.")


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
