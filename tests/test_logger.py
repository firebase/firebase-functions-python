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
"""Logger unit tests."""

from firebase_functions.logger import _replace_circular,_entry_from_args,LogSeverity,write,LogEntry
from unittest import TestCase
from unittest.mock import patch
from io import StringIO

class TestReplaceCircular(TestCase):
    """
    Tests for path utilities.
    """
    def test_basic_recursed_dict(self):

        a = {
            "foo": "bar",
        }
        a["bax"] = a

        self.assertEqual(_replace_circular(a), { "foo": "bar", "bax": "[CIRCULAR]" })

    def test_complex_recursed_dict(self):

        a = {
            "foo": "bar",
        }
        a["bax"] = a

        b = {
            "foo": "bar",
        }
        b["bax"] = a

        self.assertEqual(_replace_circular(b), { "foo": "bar", "bax": { "foo": "bar", "bax": "[CIRCULAR]"} })
    
    def test_basic_recursed_list(self):

        a = [
            "foo",
        ]
        a.append(a)

        self.assertEqual(_replace_circular(a), [ "foo", "[CIRCULAR]" ])

    def test_tuple_containing_circular(self):
            
            b = {
                "foo": "bar",
            }
            b["bax"] = b
            
            a = (
                b,
            )

            self.assertEqual(_replace_circular(a), ({'foo': 'bar', 'bax': '[CIRCULAR]'},))

    def test_immutables(self):
        self.assertEqual(_replace_circular("foo"), "foo")
        self.assertEqual(_replace_circular(1), 1)
        self.assertEqual(_replace_circular(1.0), 1.0)
        self.assertEqual(_replace_circular(True), True)
        self.assertEqual(_replace_circular(None), None)
        self.assertEqual(_replace_circular((1,)), (1,))

class TestEntryFromArgs(TestCase):
    """
    Tests for entry_from_args.
    """
    def test_basic_debug(self):
        # should this be coming through with the severity enum or as a literal string?
        self.assertEqual(_entry_from_args(LogSeverity.DEBUG,message="123"), { "message": "123", "severity": LogSeverity.DEBUG })

    def test_basic_with_kwargs(self):
        entry = _entry_from_args(LogSeverity.DEBUG,message="123",foo="bar")
        self.assertEqual(entry, { "message": "123 bar", "severity": LogSeverity.DEBUG })
    

class TestWrite(TestCase):
    """
    Tests for write.
    """
    @patch('sys.stdout', new_callable=StringIO)
    def test(self,caplog):
        entry = _entry_from_args(LogSeverity.EMERGENCY,message="123",foo="bar")

        write(entry)
        self.assertEqual(mock_stdout.getvalue(),'hello\n')