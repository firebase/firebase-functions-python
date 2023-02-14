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
from firebase_functions import options, https_fn
from firebase_functions import params
from firebase_functions.private.serving import functions_as_yaml
# pylint: disable=protected-access


@https_fn.on_call()
def asamplefunction(_):
    return "hello world"


@https_fn.on_call(preserve_external_changes=True)
def asamplefunctionpreserved(_):
    return "hello world"


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


def test_options_preserve_external_changes():
    """
    Testing if setting a global option internally change the values.
    """
    assert (options._GLOBAL_OPTIONS.preserve_external_changes is
            None), "option should not already be set"
    options.set_global_options(
        preserve_external_changes=False,
        min_instances=5,
    )
    options_asdict = options._GLOBAL_OPTIONS._asdict_with_global_options()
    assert (options_asdict["max_instances"] is
            options.RESET_VALUE), "option should be RESET_VALUE"
    assert options_asdict["min_instances"] == 5, "option should be set"

    firebase_functions = {
        "asamplefunction": asamplefunction,
    }
    yaml = functions_as_yaml(firebase_functions)
    # A quick check to make sure the yaml has null values
    # where we expect.
    assert "    availableMemoryMb: null\n" in yaml, "availableMemoryMb not in yaml"
    assert "    serviceAccountEmail: null\n" in yaml, "serviceAccountEmail not in yaml"

    firebase_functions2 = {
        "asamplefunctionpreserved": asamplefunctionpreserved,
    }
    yaml = functions_as_yaml(firebase_functions2)
    assert "    availableMemoryMb: null\n" not in yaml, "availableMemoryMb found in yaml"
    assert "    serviceAccountEmail: null\n" not in yaml, "serviceAccountEmail found in yaml"
