"""Manifest unit tests."""

import firebase_functions.manifest as _manifest
import firebase_functions.params as _params

full_endpoint = _manifest.ManifestEndpoint(
    platform="gcfv2",
    region=["us-west1"],
    availableMemoryMb=512,
    timeoutSeconds=60,
    minInstances=1,
    maxInstances=3,
    concurrency=20,
    vpc={
        "connector": "aConnector",
        "egressSettings": "ALL_TRAFFIC",
    },
    serviceAccountEmail="root@",
    ingressSettings="ALLOW_ALL",
    cpu="gcf_gen1",
    labels={
        "hello": "world",
    },
    secretEnvironmentVariables=[{
        "key": "MY_SECRET"
    }],
)

full_endpoint_dict = {
    "platform": "gcfv2",
    "region": ["us-west1"],
    "availableMemoryMb": 512,
    "timeoutSeconds": 60,
    "minInstances": 1,
    "maxInstances": 3,
    "concurrency": 20,
    "vpc": {
        "connector": "aConnector",
        "egressSettings": "ALL_TRAFFIC",
    },
    "serviceAccountEmail": "root@",
    "ingressSettings": "ALLOW_ALL",
    "cpu": "gcf_gen1",
    "labels": {
        "hello": "world",
    },
    "secretEnvironmentVariables": [{
        "key": "MY_SECRET"
    }],
}


class TestManifestEndpoint:
    """Manifest unit tests."""

    def test_endpoint_to_dict(self):
        """Generic test to check all ManifestEndpoint values convert to dict."""
        # pylint: disable=protected-access
        endpoint_dict = _manifest._dataclass_to_spec(full_endpoint)
        assert (endpoint_dict == full_endpoint_dict
               ), "Generated endpoint spec dict does not match expected dict."

    def test_endpoint_expressions(self):
        """Generic test to check all ManifestEndpoint values convert to dict."""
        expressions_test = _manifest.ManifestEndpoint(
            timeoutSeconds=_params.IntParam("hello"),
            minInstances=_params.IntParam("world"),
            maxInstances=_params.IntParam("foo"),
            concurrency=_params.IntParam("bar"),
        )
        expressions_expected_dict = {
            "platform": "gcfv2",
            "cpu": "gcf_gen1",
            "region": [],
            "secretEnvironmentVariables": [],
            "timeoutSeconds": "{{ params.hello }}",
            "minInstances": "{{ params.world }}",
            "maxInstances": "{{ params.foo }}",
            "concurrency": "{{ params.bar }}",
        }
        # pylint: disable=protected-access
        expressions_actual_dict = _manifest._dataclass_to_spec(expressions_test)
        assert (expressions_actual_dict == expressions_expected_dict
               ), "Generated endpoint spec dict does not match expected dict."
