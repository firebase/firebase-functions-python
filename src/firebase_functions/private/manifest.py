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
"""Specs for the served functions.yaml of the user's functions"""

# We're ignoring pylint's warning about names since we want
# the manifest to match the container specification.
# pylint: disable=invalid-name

import dataclasses as _dataclasses
import typing as _typing
from collections.abc import Mapping as _Mapping
from collections.abc import Sequence as _Sequence
from enum import Enum as _Enum

import typing_extensions as _typing_extensions

import firebase_functions.params as _params
import firebase_functions.private.util as _util

ManifestParamBase = _params.Param | _params.SecretParam

ManifestParam = (
    _params.BoolParam
    | _params.IntParam
    | _params._FloatParam
    | _params.ListParam
    | _params.SecretParam
    | _params.StringParam
)

SpecValue: _typing.TypeAlias = (
    str
    | int
    | float
    | bool
    | _util.Sentinel
    | list["SpecValue"]
    | dict[str, "SpecValue"]
    | None
)


class _DataclassInstance(_typing.Protocol):
    __dataclass_fields__: _typing.ClassVar[dict[str, _dataclasses.Field[object]]]


class SecretEnvironmentVariable(_typing.TypedDict):
    key: _typing_extensions.Required[str]
    secret: _typing_extensions.NotRequired[str]


class HttpsTrigger(_typing.TypedDict):
    """
    Trigger definition for arbitrary HTTPS endpoints.
    """

    invoker: _typing_extensions.NotRequired[list[str]]
    """
    Which service account should be able to trigger this function. No value means "make public"
    on create and don't do anything on update.
    """


class CallableTrigger(_typing.TypedDict):
    """
    Trigger definitions for RPCs servers using the HTTP protocol defined at
    https://firebase.google.com/docs/functions/callable-reference
    """


class EventTrigger(_typing.TypedDict):
    """
    Trigger definitions for endpoints that listen to CloudEvents emitted by
    other systems (or legacy Google events for GCF gen 1)
    """

    eventFilters: _typing_extensions.NotRequired[dict[str, str | _params.Expression[str]]]
    eventFilterPathPatterns: _typing_extensions.NotRequired[
        dict[str, str | _params.Expression[str]]
    ]
    channel: _typing_extensions.NotRequired[str]
    eventType: _typing_extensions.Required[str]
    retry: _typing_extensions.Required[bool | _params.Expression[bool] | _util.Sentinel]


class RetryConfigBase(_typing.TypedDict):
    """
    Retry configuration for a endpoint.
    """

    maxRetrySeconds: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]
    maxBackoffSeconds: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]
    maxDoublings: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]
    minBackoffSeconds: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]


class RetryConfigTasks(RetryConfigBase):
    """
    Retry configuration for a task.
    """

    maxAttempts: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]


class RetryConfigScheduler(RetryConfigBase):
    """
    Retry configuration for a schedule.
    """

    retryCount: _typing_extensions.NotRequired[
        int | _params.Expression[int] | _util.Sentinel | None
    ]


class RateLimits(_typing.TypedDict):
    maxConcurrentDispatches: int | _params.Expression[int] | _util.Sentinel | None

    maxDispatchesPerSecond: int | _params.Expression[int] | _util.Sentinel | None


class TaskQueueTrigger(_typing.TypedDict):
    """
    Trigger definitions for RPCs servers using the HTTP protocol defined at
    https://firebase.google.com/docs/functions/callable-reference
    """

    retryConfig: RetryConfigTasks | None
    rateLimits: RateLimits | None


class ScheduleTrigger(_typing.TypedDict):
    schedule: str | _params.Expression[str]
    timeZone: str | _params.Expression[str] | _util.Sentinel | None
    retryConfig: RetryConfigScheduler | None


class BlockingTriggerOptions(_typing.TypedDict):
    accessToken: _typing_extensions.NotRequired[bool]
    idToken: _typing_extensions.NotRequired[bool]
    refreshToken: _typing_extensions.NotRequired[bool]


class BlockingTrigger(_typing.TypedDict):
    eventType: _typing_extensions.Required[str]
    options: _typing_extensions.NotRequired[BlockingTriggerOptions]


class VpcSettings(_typing.TypedDict):
    connector: _typing_extensions.Required[str]
    egressSettings: _typing_extensions.NotRequired[str | _util.Sentinel]


@_dataclasses.dataclass(frozen=True)
class ManifestEndpoint:
    """A definition of a function as appears in the Manifest."""

    entryPoint: str | None = None
    region: list[str] | None = _dataclasses.field(default_factory=list[str])
    platform: str | None = "gcfv2"
    availableMemoryMb: int | _params.Expression[int] | _util.Sentinel | None = None
    maxInstances: int | _params.Expression[int] | _util.Sentinel | None = None
    minInstances: int | _params.Expression[int] | _util.Sentinel | None = None
    concurrency: int | _params.Expression[int] | _util.Sentinel | None = None
    serviceAccountEmail: str | _util.Sentinel | None = None
    timeoutSeconds: int | _params.Expression[int] | _util.Sentinel | None = None
    cpu: int | str | _util.Sentinel | None = None
    vpc: VpcSettings | None = None
    labels: dict[str, str] | None = None
    ingressSettings: str | None | _util.Sentinel = None
    secretEnvironmentVariables: list[SecretEnvironmentVariable] | _util.Sentinel | None = (
        _dataclasses.field(default_factory=list[SecretEnvironmentVariable])
    )
    httpsTrigger: HttpsTrigger | None = None
    callableTrigger: CallableTrigger | None = None
    eventTrigger: EventTrigger | None = None
    scheduleTrigger: ScheduleTrigger | None = None
    blockingTrigger: BlockingTrigger | None = None
    taskQueueTrigger: TaskQueueTrigger | None = None


class ManifestRequiredApi(_typing.TypedDict):
    api: _typing_extensions.Required[str]
    reason: _typing_extensions.Required[str]


@_dataclasses.dataclass(frozen=True)
class ManifestStack:
    endpoints: dict[str, ManifestEndpoint]
    specVersion: str = "v1alpha1"
    params: _Sequence[ManifestParamBase] | None = _dataclasses.field(default_factory=list[ManifestParamBase])
    requiredAPIs: list[ManifestRequiredApi] = _dataclasses.field(
        default_factory=list[ManifestRequiredApi]
    )


def _param_input_to_spec(
    param_input: _params.TextInput
    | _params.ResourceInput
    | _params.SelectInput
    | _params.MultiSelectInput,
) -> dict[str, SpecValue]:
    if isinstance(param_input, _params.TextInput):
        return {
            "text": {
                key: value
                for key, value in {
                    "example": param_input.example,
                    "validationRegex": param_input.validation_regex,
                    "validationErrorMessage": param_input.validation_error_message,
                }.items()
                if value is not None
            }
        }

    if isinstance(param_input, _params.ResourceInput):
        return {
            "resource": {
                "type": param_input.type,
            },
        }

    if isinstance(param_input, _params.MultiSelectInput | _params.SelectInput):
        key = "select" if isinstance(param_input, _params.SelectInput) else "multiSelect"
        return {
            key: {
                "options": [
                    {
                        key: value
                        for key, value in {
                            "value": option.value,
                            "label": option.label,
                        }.items()
                        if value is not None
                    }
                    for option in param_input.options
                ],
            },
        }

    return {}


def _param_to_spec(param: ManifestParamBase) -> dict[str, SpecValue]:
    spec_dict: dict[str, SpecValue] = {
        "name": param.name,
        "label": param.label,
        "description": param.description,
        "immutable": param.immutable,
    }

    if isinstance(param, _params.Param):
        spec_dict["default"] = (
            f"{param.default}" if isinstance(param.default, _params.Expression) else param.default
        )
        if param.input:
            spec_dict["input"] = _param_input_to_spec(param.input)

    if isinstance(param, _params.BoolParam):
        spec_dict["type"] = "boolean"
    elif isinstance(param, _params.IntParam):
        spec_dict["type"] = "int"
    elif isinstance(param, _params._FloatParam):
        spec_dict["type"] = "float"
    elif isinstance(param, _params.SecretParam):
        spec_dict["type"] = "secret"
    elif isinstance(param, _params.ListParam):
        spec_dict["type"] = "list"
    elif isinstance(param, _params.StringParam):
        spec_dict["type"] = "string"
    else:
        raise NotImplementedError("Unsupported param type.")

    return _dict_to_spec(spec_dict)


def _object_to_spec(data: object) -> SpecValue:
    if isinstance(data, _Enum):
        return data.value
    elif isinstance(data, _params.Expression):
        return f"{data}"
    elif _dataclasses.is_dataclass(data):
        return _dataclass_to_spec(_typing.cast(_DataclassInstance, data))
    elif isinstance(data, list):
        return list(map(_object_to_spec, data))
    elif isinstance(data, dict):
        return _dict_to_spec(data)
    elif data is None:
        return None
    elif isinstance(data, _util.Sentinel):
        return data
    elif isinstance(data, (str, int, float, bool)):
        return data
    else:
        raise TypeError(f"Unsupported manifest spec value: {type(data)!r}")


def _dict_factory(data: list[tuple[str, object]]) -> dict[str, SpecValue]:
    out: dict[str, SpecValue] = {}
    for key, value in data:
        if value is not None:
            out[key] = _object_to_spec(value)
    return out


def _dataclass_to_spec(data: _DataclassInstance) -> dict[str, SpecValue]:
    out: dict[str, SpecValue] = {}
    for field in _dataclasses.fields(data):
        value = _object_to_spec(getattr(data, field.name))
        if value is not None:
            out[field.name] = value
    return out


def _dict_to_spec(data: _Mapping[str, object]) -> dict[str, SpecValue]:
    return _dict_factory(list(data.items()))


def manifest_to_spec_dict(manifest: ManifestStack) -> dict[str, SpecValue]:
    params = manifest.params
    out: dict[str, SpecValue] = _dataclass_to_spec(manifest)
    if params is not None:
        out["params"] = list(map(_param_to_spec, params))
    return out
