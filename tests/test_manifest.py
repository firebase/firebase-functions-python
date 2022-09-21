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

full_stack = _manifest.ManifestStack(
    endpoints={"test": full_endpoint},
    params=[
        _params.BoolParam("bool_test", default=False),
        _params.IntParam("int_test", description="int_description"),
        _params.FloatParam("float_test", immutable=True),
        _params.SecretParam("secret_test"),
        _params.StringParam("string_test"),
        _params.ListParam("list_test", default=["1", "2", "3"]),
    ],
    requiredApis=[{
        "api": "test_api",
        "reason": "testing"
    }])

full_stack_dict = {
    "specVersion": "v1alpha1",
    "endpoints": {
        "test": full_endpoint_dict
    },
    "params": [{
        "name": "bool_test",
        "type": "boolean",
        "default": False,
    }, {
        "name": "int_test",
        "type": "int",
        "description": "int_description"
    }, {
        "name": "float_test",
        "type": "float",
        "immutable": True,
    }, {
        "name": "secret_test",
        "type": "secret"
    }, {
        "name": "string_test",
        "type": "string"
    }, {
        "default": "1,2,3",
        "name": "list_test",
        "type": "list"
    }],
    "requiredApis": [{
        "api": "test_api",
        "reason": "testing"
    }]
}


class TestManifestStack:
    """Stack unit tests."""

    def test_stack_to_dict(self):
        """Generic check that all ManifestStack values convert to dict."""
        # pylint: disable=protected-access
        stack_dict = _manifest._manifest_to_spec(full_stack)
        assert (stack_dict == full_stack_dict
               ), "Generated manifest spec dict does not match expected dict."


class TestManifestEndpoint:
    """Manifest unit tests."""

    def test_endpoint_to_dict(self):
        """Generic check that all ManifestEndpoint values convert to dict."""
        # pylint: disable=protected-access
        endpoint_dict = _manifest._dataclass_to_spec(full_endpoint)
        assert (endpoint_dict == full_endpoint_dict
               ), "Generated endpoint spec dict does not match expected dict."

    def test_endpoint_expressions(self):
        """Check Expression values convert to CEL strings."""
        expressions_test = _manifest.ManifestEndpoint(
            availableMemoryMb=_params.TernaryExpression(
                _params.BoolParam("large"), 1024, 256),
            minInstances=_params.StringParam("large").equals("yes").then(6, 1),
            maxInstances=_params.IntParam("max").compare(">", 6).then(
                6, _params.IntParam("max")),
            timeoutSeconds=_params.IntParam("world"),
            concurrency=_params.IntParam("bar"),
            vpc={"connector": _params.SecretParam("secret")})
        expressions_expected_dict = {
            "platform": "gcfv2",
            "cpu": "gcf_gen1",
            "region": [],
            "secretEnvironmentVariables": [],
            "availableMemoryMb": "{{ params.large ? 1024 : 256 }}",
            "minInstances": "{{ params.large == \"yes\" ? 6 : 1 }}",
            "maxInstances": "{{ params.max > 6 ? 6 : params.max }}",
            "timeoutSeconds": "{{ params.world }}",
            "concurrency": "{{ params.bar }}",
            "vpc": {
                "connector": "{{ params.secret }}"
            }
        }
        # pylint: disable=protected-access
        expressions_actual_dict = _manifest._dataclass_to_spec(expressions_test)
        assert (expressions_actual_dict == expressions_expected_dict
               ), "Generated endpoint spec dict does not match expected dict."

    def test_endpoint_nones(self):
        """Check all None values are removed."""
        expressions_test = _manifest.ManifestEndpoint(
            timeoutSeconds=None,
            minInstances=None,
            maxInstances=None,
            concurrency=None,
        )
        expressions_expected_dict = {
            "platform": "gcfv2",
            "cpu": "gcf_gen1",
            "region": [],
            "secretEnvironmentVariables": [],
        }
        # pylint: disable=protected-access
        expressions_actual_dict = _manifest._dataclass_to_spec(expressions_test)
        assert (expressions_actual_dict == expressions_expected_dict
               ), "Generated endpoint spec dict does not match expected dict."
