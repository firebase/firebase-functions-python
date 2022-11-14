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
Options unit tests.
"""
from firebase_functions import options
from firebase_functions import params
# pylint: disable=protected-access


def test_set_global_options():
    """
    Testing if setting a global option internally change the values.
    """
    assert options._GLOBAL_OPTIONS.max_instances is None, "option should not already be set"
    options.set_global_options(max_instances=2)
    assert options._GLOBAL_OPTIONS.max_instances == 2, "option was not set"


def test_global_options_merged_with_provider_options():
    """
    Testing a global option is used when no provider option is set.
    """
    options.set_global_options(max_instances=66)
    pubsub_options = options.PubSubOptions(topic="foo")  #pylint: disable=unexpected-keyword-arg
    pubsub_options_dict = pubsub_options._asdict_with_global_options()
    assert (pubsub_options_dict["topic"] == "foo"
           ), "'topic' property missing from dict"
    assert "options" not in pubsub_options_dict, "'options' key should not exist in dict"
    assert (pubsub_options_dict["max_instances"] == 66
           ), "provider option did not update using the global option"


def test_https_options_removes_cors():
    """
    Testing _HttpsOptions strips out the 'cors' property when converted to a dict.
    """
    https_options = options.HttpsOptions(cors=options.CorsOptions(
        cors_origins="*"))
    assert https_options.cors.cors_origins == "*", "cors options were not set"
    https_options_dict = https_options._asdict_with_global_options()
    assert "cors" not in https_options_dict, "'cors' key should not exist in dict"


def test_options_asdict_uses_cel_representation():
    """
    Test Param or Expression option values are converted to their
    CEL values for manifest representation.
    """
    int_param = params.IntParam("MIN")
    https_options_dict = options.HttpsOptions(
        min_instances=int_param)._asdict_with_global_options()
    assert https_options_dict["min_instances"] == int_param.to_cel(
    ), "param was not converted to CEL string"
