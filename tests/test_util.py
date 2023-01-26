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
from firebase_functions.private.util import firebase_config

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
