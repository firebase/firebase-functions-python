"""
Options unit tests.
"""
from firebase_functions import options
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
