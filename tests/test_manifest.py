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
"""Manifest unit tests."""

import firebase_functions.private.manifest as _manifest
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
        _params.BoolParam("BOOL_TEST", default=False),
        _params.IntParam("INT_TEST", description="int_description"),
        _params.FloatParam("FLOAT_TEST", immutable=True),
        _params.SecretParam("SECRET_TEST"),
        _params.StringParam("STRING_TEST"),
    ],
    requiredAPIs=[{
        "api": "test_api",
        "reason": "testing"
    }],
)

full_stack_dict = {
    "specVersion": "v1alpha1",
    "endpoints": {
        "test": full_endpoint_dict
    },
    "params": [
        {
            "name": "BOOL_TEST",
            "type": "boolean",
            "default": False,
        },
        {
            "name": "INT_TEST",
            "type": "int",
            "description": "int_description"
        },
        {
            "name": "FLOAT_TEST",
            "type": "float",
            "immutable": True,
        },
        {
            "name": "SECRET_TEST",
            "type": "secret"
        },
        {
            "name": "STRING_TEST",
            "type": "string"
        },
    ],
    "requiredAPIs": [{
        "api": "test_api",
        "reason": "testing"
    }]
}


class TestManifestStack:
    """Stack unit tests."""

    def test_stack_to_dict(self):
        """Generic check that all ManifestStack values convert to dict."""
        stack_dict = _manifest.manifest_to_spec_dict(full_stack)
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
        max_param = _params.IntParam("MAX")
        expressions_test = _manifest.ManifestEndpoint(
            availableMemoryMb=_params.TernaryExpression(
                _params.BoolParam("LARGE_BOOL"), 1024, 256),
            minInstances=_params.StringParam("LARGE_STR").equals("yes").then(
                6, 1),
            maxInstances=max_param.compare(">", 6).then(6, max_param),
            timeoutSeconds=_params.IntParam("WORLD"),
            concurrency=_params.IntParam("BAR"),
            vpc={"connector": _params.SecretParam("SECRET")})
        expressions_expected_dict = {
            "platform": "gcfv2",
            "region": [],
            "secretEnvironmentVariables": [],
            "availableMemoryMb": "{{ params.LARGE_BOOL ? 1024 : 256 }}",
            "minInstances": "{{ params.LARGE_STR == \"yes\" ? 6 : 1 }}",
            "maxInstances": "{{ params.MAX > 6 ? 6 : params.MAX }}",
            "timeoutSeconds": "{{ params.WORLD }}",
            "concurrency": "{{ params.BAR }}",
            "vpc": {
                "connector": "{{ params.SECRET }}"
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
            "region": [],
            "secretEnvironmentVariables": [],
        }
        # pylint: disable=protected-access
        expressions_actual_dict = _manifest._dataclass_to_spec(expressions_test)
        assert (expressions_actual_dict == expressions_expected_dict
               ), "Generated endpoint spec dict does not match expected dict."
