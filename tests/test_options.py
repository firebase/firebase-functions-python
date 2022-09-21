"""
Options unit tests.
"""
from firebase_functions import options


def test_set_global_options():
    """
    Testing if setting the global options actually change the values.
    """
    options.set_global_options(max_instances=1)

    assert options.GLOBAL_OPTIONS.max_instances == 1


def test_https_options():
    """
    Testing if setting the global options actually change the values.
    """
    options.set_global_options(max_instances=1)

    assert options.GLOBAL_OPTIONS.max_instances == 1

    https_options_1 = options.HttpsOptions()

    assert https_options_1.max_instances == options.GLOBAL_OPTIONS.max_instances

    https_options_2 = options.HttpsOptions(max_instances=3)

    assert https_options_2.max_instances != options.GLOBAL_OPTIONS.max_instances


def test_pubsub_options():
    """
    Testing if setting the global options actually change the values.
    """
    options.set_global_options(max_instances=1)

    assert options.GLOBAL_OPTIONS.max_instances == 1

    pubsub_options_1 = options.PubSubOptions()

    assert pubsub_options_1.max_instances == options.GLOBAL_OPTIONS.max_instances

    pubsub_options_2 = options.PubSubOptions(topic="Hi", max_instances=3)

    assert pubsub_options_2.max_instances != options.GLOBAL_OPTIONS.max_instances
