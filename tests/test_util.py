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

import pytest

from firebase_functions.private.util import (
    PrecisionTimestamp,
    _unsafe_decode_id_token,
    deep_merge,
    firebase_config,
    get_precision_timestamp,
    microsecond_timestamp_conversion,
    nanoseconds_timestamp_conversion,
    normalize_path,
    second_timestamp_conversion,
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
        expected_datetime = _dt.datetime.strptime(expected_output, "%Y-%m-%dT%H:%M:%S.%fZ")
        expected_datetime = expected_datetime.replace(tzinfo=_dt.timezone.utc)
        assert microsecond_timestamp_conversion(input_timestamp) == expected_datetime


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
        expected_datetime = _dt.datetime.strptime(expected_output, "%Y-%m-%dT%H:%M:%S.%fZ")
        expected_datetime = expected_datetime.replace(tzinfo=_dt.timezone.utc)
        assert nanoseconds_timestamp_conversion(input_timestamp) == expected_datetime


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
        expected_datetime = _dt.datetime.strptime(expected_output, "%Y-%m-%dT%H:%M:%SZ")
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

    assert get_precision_timestamp(microsecond_timestamp1) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(microsecond_timestamp2) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(microsecond_timestamp3) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(microsecond_timestamp4) is PrecisionTimestamp.MICROSECONDS
    assert get_precision_timestamp(nanosecond_timestamp1) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(nanosecond_timestamp2) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(nanosecond_timestamp3) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(nanosecond_timestamp4) is PrecisionTimestamp.NANOSECONDS
    assert get_precision_timestamp(second_timestamp1) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(second_timestamp2) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(second_timestamp3) is PrecisionTimestamp.SECONDS
    assert get_precision_timestamp(second_timestamp4) is PrecisionTimestamp.SECONDS


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


# Helper class for timestamp conversion tests
class _Timestamp:
    """Helper class to simulate Firebase Timestamp objects."""

    def __init__(self, seconds: int, nanoseconds: int):
        self.seconds = seconds
        self.nanoseconds = nanoseconds


def _assert_utc_datetime(dt: _dt.datetime) -> None:
    """Helper to assert datetime is UTC timezone-aware."""
    assert dt.tzinfo == _dt.timezone.utc


@pytest.mark.parametrize(
    "seconds,nanoseconds,expected_str",
    [
        (0, 0, "1970-01-01T00:00:00.000000+00:00"),  # The epoch
        (1, 0, "1970-01-01T00:00:01.000000+00:00"),  # 1 second after epoch
        (0, 1, "1970-01-01T00:00:00.000000+00:00"),  # 1 nanosecond (truncated)
        (0, 999_999, "1970-01-01T00:00:00.000999+00:00"),  # < 1 microsecond
        (0, 1_000, "1970-01-01T00:00:00.000001+00:00"),  # 1 microsecond
        (0, 999_999_999, "1970-01-01T00:00:00.999999+00:00"),  # almost 1 second
        (0, 1_000_000_000, "1970-01-01T00:00:01.000000+00:00"),  # exactly 1 second (carries)
        (123456, 1_500_000_000, "1970-01-02T10:17:37.500000+00:00"),  # overflow with remainder
        (1672578896, 123456789, "2023-01-01T13:14:56.123456+00:00"),  # real-world example
        (-1, 0, "1969-12-31T23:59:59.000000+00:00"),  # 1 second before epoch
        (-1, 500_000_000, "1969-12-31T23:59:59.500000+00:00"),  # negative seconds, positive nsec
    ],
)
def test_timestamp_conversion_object_known_cases(seconds: int, nanoseconds: int, expected_str: str):
    """Test timestamp_conversion with objects using known correct expected values."""
    timestamp_obj = _Timestamp(seconds=seconds, nanoseconds=nanoseconds)
    result = timestamp_conversion(timestamp_obj)
    expected = _dt.datetime.fromisoformat(expected_str)
    assert result == expected
    _assert_utc_datetime(result)


@pytest.mark.parametrize(
    "seconds,nanoseconds",
    [
        (123456, -500_000_000),  # negative nanoseconds
        (123456, 2_999_999_999),  # large nanoseconds, multiple second carry
        (2_147_483_647, 0),  # max 32-bit int
        (-2, 2_000_000_000),  # negative seconds, nanoseconds w/ carry
        (0, -1),  # negative nanoseconds underflow
        (0, -1_000_000_000),  # underflow full second
        (0, -1_500_000_000),  # underflow more than one second
        (1687256122, 396358000),  # nominal case
        (1687256122, 0),
        (0, 0),
        (0, 1),
        (0, 999_999_999),
        (1687256122, 2_000_000_000),
        (1687256122, -500_000_000),
        (-1, 999_999_999),
        (-1, 500_000_000),
        (-2, 2_000_000_000),
        (2_147_483_647, 999_999_999),
        (-2_147_483_648, 0),
        (0, -2_000_000_000),
        (0, 2_000_000_000),
    ],
)
def test_timestamp_conversion_object_dict_consistency(seconds: int, nanoseconds: int):
    """Test that object and dict branches produce identical results."""
    timestamp_obj = _Timestamp(seconds=seconds, nanoseconds=nanoseconds)
    timestamp_dict = {"seconds": seconds, "nanoseconds": nanoseconds}

    result_obj = timestamp_conversion(timestamp_obj)
    result_dict = timestamp_conversion(timestamp_dict)

    assert result_obj == result_dict
    _assert_utc_datetime(result_obj)
    _assert_utc_datetime(result_dict)


@pytest.mark.parametrize(
    "seconds,nanoseconds",
    [
        (1672576496, 123456000),  # nanoseconds already in microsecond precision
        (1672576496, 0),
        (1672576496, 999999000),
    ],
)
def test_timestamp_conversion_string_cross_validation(seconds: int, nanoseconds: int):
    """Test cross-validation with string path for microsecond-precision nanoseconds."""
    dt_from_obj = timestamp_conversion(_Timestamp(seconds=seconds, nanoseconds=nanoseconds))
    iso_str = dt_from_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    dt_from_string = timestamp_conversion(iso_str)

    assert dt_from_obj == dt_from_string


@pytest.mark.parametrize(
    "timestamp_str,conversion_func",
    [
        ("2023-01-01T12:34:56.123456789Z", nanoseconds_timestamp_conversion),
        ("2023-06-20T10:15:22.396358Z", microsecond_timestamp_conversion),
        ("2023-01-01T12:34:56Z", second_timestamp_conversion),
    ],
)
def test_timestamp_conversion_with_string(timestamp_str: str, conversion_func):
    """Test timestamp_conversion works with string inputs."""
    result = timestamp_conversion(timestamp_str)
    expected = conversion_func(timestamp_str)
    assert result == expected
    _assert_utc_datetime(result)


@pytest.mark.parametrize(
    "invalid_input,expected_error_msg",
    [
        (12345, "timestamp_conversion expects a string or a Timestamp-like object"),
        ("invalid_timestamp", None),  # Error message varies, just check ValueError
        (None, None),
    ],
)
def test_timestamp_conversion_errors(invalid_input, expected_error_msg):
    """Test timestamp_conversion raises appropriate errors for invalid inputs."""
    with pytest.raises(ValueError) as exc_info:
        timestamp_conversion(invalid_input)
    if expected_error_msg:
        assert expected_error_msg in str(exc_info.value)


def test_timestamp_conversion_error_missing_seconds():
    """Test timestamp_conversion raises error when seconds attribute is missing."""

    class IncompleteTimestamp:
        def __init__(self, nanoseconds: int):
            self.nanoseconds = nanoseconds

    with pytest.raises(ValueError):
        timestamp_conversion(IncompleteTimestamp(nanoseconds=123456789))


def test_timestamp_conversion_error_missing_nanoseconds():
    """Test timestamp_conversion raises error when nanoseconds key is missing in dict."""
    with pytest.raises(ValueError):
        timestamp_conversion({"nanoseconds": 123456789})
