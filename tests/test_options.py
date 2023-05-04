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
from firebase_functions.private.serving import functions_as_yaml, merge_required_apis
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
    assert https_options_dict[
        "min_instances"] == f"{int_param}", "param was not converted to CEL string"


def test_options_preserve_external_changes():
    """
    Testing if setting a global option internally change the values.
    """
    assert (options._GLOBAL_OPTIONS.preserve_external_changes
            is None), "option should not already be set"
    options.set_global_options(
        preserve_external_changes=False,
        min_instances=5,
    )
    options_asdict = options._GLOBAL_OPTIONS._asdict_with_global_options()
    assert (options_asdict["max_instances"]
            is options.RESET_VALUE), "option should be RESET_VALUE"
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


def test_merge_apis_empty_input():
    """
    This test checks the behavior of the merge_required_apis function
    when the input is an empty list. The desired outcome for this test
    is to receive an empty list as output. This test ensures that the
    function can handle the situation where there are no input APIs to merge.
    """
    required_apis = []
    expected_output = []
    merged_apis = merge_required_apis(required_apis)

    assert merged_apis == expected_output, f"Expected {expected_output}, but got {merged_apis}"


def test_merge_apis_no_duplicate_apis():
    """
    This test verifies that the merge_required_apis function functions
    correctly when the input is a list of unique APIs with no duplicates.
    The expected result is a list containing the same unique APIs in the
    input list. This test confirms that the function processes and returns
    APIs without modification when there is no duplication.
    """
    required_apis = [
        {
            "api": "API1",
            "reason": "Reason 1"
        },
        {
            "api": "API2",
            "reason": "Reason 2"
        },
        {
            "api": "API3",
            "reason": "Reason 3"
        },
    ]

    expected_output = [
        {
            "api": "API1",
            "reason": "Reason 1"
        },
        {
            "api": "API2",
            "reason": "Reason 2"
        },
        {
            "api": "API3",
            "reason": "Reason 3"
        },
    ]

    merged_apis = merge_required_apis(required_apis)

    assert merged_apis == expected_output, f"Expected {expected_output}, but got {merged_apis}"


def test_merge_apis_duplicate_apis():
    """
    This test evaluates the merge_required_apis function when the
    input list contains duplicate APIs with different reasons.
    The desired outcome for this test is a list where the duplicate
    APIs are merged properly and reasons are combined. 
    This test ensures that the function correctly merges the duplicate
    APIs and combines the reasons associated with them.
    """
    required_apis = [
        {
            "api": "API1",
            "reason": "Reason 1"
        },
        {
            "api": "API2",
            "reason": "Reason 2"
        },
        {
            "api": "API1",
            "reason": "Reason 3"
        },
        {
            "api": "API2",
            "reason": "Reason 4"
        },
    ]

    expected_output = [
        {
            "api": "API1",
            "reason": "Reason 1 Reason 3"
        },
        {
            "api": "API2",
            "reason": "Reason 2 Reason 4"
        },
    ]

    merged_apis = merge_required_apis(required_apis)

    assert len(merged_apis) == len(
        expected_output
    ), f"Expected a list of length {len(expected_output)}, but got {len(merged_apis)}"

    for expected_item in expected_output:
        assert (expected_item in merged_apis
               ), f"Expected item {expected_item} missing from the merged list"

    for actual_item in merged_apis:
        assert (actual_item in expected_output
               ), f"Unexpected item {actual_item} found in the merged list"
