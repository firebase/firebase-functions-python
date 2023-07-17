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
"""Path Pattern unit tests."""

from unittest import TestCase
from firebase_functions.private.path_pattern import path_parts, PathPattern, trim_param


class TestPathUtilities(TestCase):
    """
    Tests for path utilities.
    """

    def test_path_parts(self):
        self.assertEqual(["foo", "bar", "baz"], path_parts("/foo/bar/baz"))
        self.assertEqual([], path_parts(""))
        self.assertEqual([], path_parts(None))
        self.assertEqual([], path_parts("/"))


class TestPathPattern(TestCase):
    """
    Tests for PathPattern.
    """

    def test_trim_param(self):
        # trim a capture without equals
        self.assertEqual(trim_param("{something}"), "something")
        # trim a capture with equals
        self.assertEqual(trim_param("{something=*}"), "something")

    def test_extract_matches(self):
        # parse single-capture segments with leading slash
        pp = PathPattern("/messages/{a}/{b}/{c}")
        self.assertEqual(
            pp.extract_matches("messages/match_a/match_b/match_c"),
            {
                "a": "match_a",
                "b": "match_b",
                "c": "match_c",
            },
        )

        # parse single-capture segments without leading slash
        pp = PathPattern("messages/{a}/{b}/{c}")
        self.assertEqual(
            pp.extract_matches("messages/match_a/match_b/match_c"),
            {
                "a": "match_a",
                "b": "match_b",
                "c": "match_c",
            },
        )

        # parse without multi-capture segments
        pp = PathPattern("{a}/something/else/{b}/end/{c}")
        self.assertEqual(
            pp.extract_matches("match_a/something/else/match_b/end/match_c"),
            {
                "a": "match_a",
                "b": "match_b",
                "c": "match_c",
            },
        )

        # parse multi segment with params after
        pp = PathPattern("something/**/else/{a}/hello/{b}/world")
        self.assertEqual(
            pp.extract_matches(
                "something/is/a/thing/else/nothing/hello/user/world"),
            {
                "a": "nothing",
                "b": "user",
            },
        )

        # parse multi-capture segment with params after
        pp = PathPattern("something/{path=**}/else/{a}/hello/{b}/world")
        self.assertEqual(
            pp.extract_matches(
                "something/is/a/thing/else/nothing/hello/user/world"),
            {
                "path": "is/a/thing",
                "a": "nothing",
                "b": "user",
            },
        )

        # parse multi segment with params before
        pp = PathPattern("{a}/something/{b}/**/end")
        self.assertEqual(
            pp.extract_matches(
                "match_a/something/match_b/thing/else/nothing/hello/user/end"),
            {
                "a": "match_a",
                "b": "match_b",
            },
        )

        # parse multi-capture segment with params before
        pp = PathPattern("{a}/something/{b}/{path=**}/end")
        self.assertEqual(
            pp.extract_matches(
                "match_a/something/match_b/thing/else/nothing/hello/user/end"),
            {
                "a": "match_a",
                "b": "match_b",
                "path": "thing/else/nothing/hello/user",
            },
        )

        # parse multi segment with params before and after
        pp = PathPattern("{a}/something/**/{b}/end")
        self.assertEqual(
            pp.extract_matches(
                "match_a/something/thing/else/nothing/hello/user/match_b/end"),
            {
                "a": "match_a",
                "b": "match_b",
            },
        )

        # parse multi-capture segment with params before and after
        pp = PathPattern("{a}/something/{path=**}/{b}/end")
        self.assertEqual(
            pp.extract_matches(
                "match_a/something/thing/else/nothing/hello/user/match_b/end"),
            {
                "a": "match_a",
                "b": "match_b",
                "path": "thing/else/nothing/hello/user",
            },
        )

        pp = PathPattern("{a}-something-{b}-else-{c}")
        self.assertEqual(
            pp.extract_matches("match_a-something-match_b-else-match_c"),
            {},
        )

        pp = PathPattern("{a}")
        self.assertEqual(
            pp.extract_matches("match_a"),
            {
                "a": "match_a",
            },
        )
