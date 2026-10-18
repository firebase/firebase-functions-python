# Copyright 2024 Google Inc.
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
Tests for internal alerts utility functions.
"""

import datetime as _dt

import pytest

from firebase_functions.private._alerts_fn import (
    _parse_digest_date,
    stability_digest_payload_from_ce_payload,
)


def test_parse_digest_date_valid_calendar_date():
    """
    Testing that valid {year, month, day} calendar dates are parsed
    into timezone-aware UTC datetime at midnight.
    """
    date_dict = {"year": 2026, "month": 5, "day": 15}
    expected = _dt.datetime(2026, 5, 15, 0, 0, tzinfo=_dt.timezone.utc)
    assert _parse_digest_date(date_dict) == expected


def test_parse_digest_date_valid_timestamp_dict():
    """
    Testing that valid timestamp dictionaries are accepted.
    """
    ts_dict = {"seconds": 1712750400, "nanos": 0}
    expected = _dt.datetime(2024, 4, 10, 12, 0, tzinfo=_dt.timezone.utc)
    assert _parse_digest_date(ts_dict) == expected

    ts_dict_nanos = {"seconds": 1712750400, "nanos": 123456000}
    expected_nanos = _dt.datetime(2024, 4, 10, 12, 0, 0, 123456, tzinfo=_dt.timezone.utc)
    assert _parse_digest_date(ts_dict_nanos) == expected_nanos


def test_parse_digest_date_valid_iso_string():
    """
    Testing that valid ISO 8601 string representations are supported.
    """
    iso_str = "2026-05-15T00:00:00Z"
    expected = _dt.datetime(2026, 5, 15, 0, 0, tzinfo=_dt.timezone.utc)
    assert _parse_digest_date(iso_str) == expected


def test_parse_digest_date_missing_fields_raises():
    """
    Testing that missing calendar-date fields raise ValueError.
    """
    incomplete_dates = [
        {"year": 2026, "month": 5},
        {"year": 2026, "day": 15},
        {"month": 5, "day": 15},
    ]
    for d in incomplete_dates:
        with pytest.raises(ValueError):
            _parse_digest_date(d)


def test_parse_digest_date_explicit_none_raises():
    """
    Testing that explicit None calendar-date fields raise ValueError.
    """
    none_dates = [
        {"year": None, "month": 5, "day": 15},
        {"year": 2026, "month": None, "day": 15},
        {"year": 2026, "month": 5, "day": None},
    ]
    for d in none_dates:
        with pytest.raises(ValueError):
            _parse_digest_date(d)


def test_parse_digest_date_invalid_values_raises():
    """
    Testing that invalid month, day, or non-integer values raise ValueError.
    """
    invalid_dates = [
        {"year": 2026, "month": 13, "day": 15},
        {"year": 2026, "month": 2, "day": 30},
        {"year": 2026, "month": 0, "day": 15},
        {"year": 2026, "month": 5, "day": 32},
        {"year": "invalid", "month": 5, "day": 15},
    ]
    for d in invalid_dates:
        with pytest.raises(ValueError):
            _parse_digest_date(d)


def test_parse_digest_date_unrecognized_dict_raises():
    """
    Testing that empty or unknown dictionaries raise ValueError.
    """
    bad_dicts = [
        {},
        {"foo": "bar"},
        {"digestDate": "2026-05-15"},
    ]
    for d in bad_dicts:
        with pytest.raises(ValueError):
            _parse_digest_date(d)


def test_parse_digest_date_invalid_types_raises():
    """
    Testing that non-string and non-dict types raise ValueError.
    """
    bad_types = [
        12345,
        123.45,
        ["2026", "05", "15"],
        None,
    ]
    for val in bad_types:
        with pytest.raises(ValueError):
            _parse_digest_date(val)


def test_stability_digest_payload_from_ce_payload():
    """
    Testing stability_digest_payload_from_ce_payload parses full payload with calendar date.
    """
    ce_payload = {
        "digestDate": {"year": 2026, "month": 5, "day": 15},
        "trendingIssues": [
            {
                "type": "crash",
                "issue": {
                    "id": "issue-123",
                    "title": "NullPointerException",
                    "subtitle": "MainActivity.kt:42",
                    "appVersion": "1.0.0",
                },
                "eventCount": 42,
                "userCount": 10,
            }
        ],
    }
    payload = stability_digest_payload_from_ce_payload(ce_payload)
    assert payload.digest_date == _dt.datetime(2026, 5, 15, 0, 0, tzinfo=_dt.timezone.utc)
    assert len(payload.trending_issues) == 1
    assert payload.trending_issues[0].event_count == 42
    assert payload.trending_issues[0].issue.id == "issue-123"
