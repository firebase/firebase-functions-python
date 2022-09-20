"""Specs for the served functions.yaml of the user's functions"""

# We're ignoring pylint's warning about names since we want
# the manifest to match the container specification.

# pylint: disable=invalid-name

from dataclasses import dataclass
from typing import TypedDict, Optional, Union
from typing_extensions import NotRequired, Required

from firebase_functions.params import Expression, Param


class SecretEnvironmentVariable(TypedDict):
    key: Required[str]
    secret: NotRequired[str]


class HttpsTrigger(TypedDict):
    """
    Trigger definition for arbitrary HTTPS endpoints.
    """
    invoker: NotRequired[list[str]]
    """
    Which service account should be able to trigger this function. No value means "make public"
    on create and don't do anything on update.
    """


class CallableTrigger(TypedDict):
    """
    Trigger definitions for RPCs servers using the HTTP protocol defined at
    https://firebase.google.com/docs/functions/callable-reference
    """


class EventTrigger(TypedDict):
    """
    Trigger definitions for endpoints that listen to CloudEvents emitted by
    other systems (or legacy Google events for GCF gen 1)
    """
    eventFilters: NotRequired[dict[str, Union[str, Expression[str]]]]
    eventFilterPathPatterns: NotRequired[dict[str, Union[str, Expression[str]]]]
    channel: NotRequired[str]
    eventType: Required[str]
    retry: Required[Union[bool, Expression[bool]]]
    region: NotRequired[str]
    serviceAccountEmail: NotRequired[str]


class RetryConfig(TypedDict):
    retryCount: NotRequired[Union[int, Expression[int]]]
    maxRetrySeconds: NotRequired[Union[str, Expression[str]]]
    minBackoffSeconds: NotRequired[Union[str, Expression[str]]]
    maxBackoffSeconds: NotRequired[Union[str, Expression[str]]]
    maxDoublings: NotRequired[Union[int, Expression[int]]]


class ScheduleTrigger(TypedDict):
    schedule: NotRequired[Union[str, Expression[str]]]
    timeZone: NotRequired[Union[str, Expression[str]]]
    retryConfig: NotRequired[RetryConfig]


class BlockingTrigger(TypedDict):
    eventType: Required[str]


class VpcSettings(TypedDict):
    connector: Required[Union[str, Expression[str]]]
    egressSettings: NotRequired[str]


@dataclass(frozen=True)
class ManifestEndpoint:
    """An definition of a function as appears in the Manifest."""

    entryPoint: Optional[str] = None
    region: Optional[list[str]] = None
    platform: Optional[str] = "gcfv2"
    availableMemoryMb: Union[int, Expression[int], None] = None
    maxInstances: Union[int, Expression[int], None] = None
    minInstances: Union[int, Expression[int], None] = None
    concurrency: Union[int, Expression[int], None] = None
    serviceAccountEmail: Optional[str] = None
    timeoutSeconds: Union[int, Expression[int], None] = None
    cpu: Union[int, str] = "gcf_gen1"
    vpc: Optional[VpcSettings] = None
    labels: Optional[dict[str, str]] = None
    ingressSettings: Optional[str] = None
    environmentVariables: Optional[dict[str, str]] = None
    secretEnvironmentVariables: Optional[list[SecretEnvironmentVariable]] = None
    httpsTrigger: Optional[HttpsTrigger] = None
    callableTrigger: Optional[CallableTrigger] = None
    eventTrigger: Optional[EventTrigger] = None
    scheduleTrigger: Optional[ScheduleTrigger] = None
    blockingTrigger: Optional[BlockingTrigger] = None


class ManifestRequiredApi(TypedDict):
    api: Required[str]
    reason: Required[str]


@dataclass(frozen=True)
class ManifestStack:
    endpoints: dict[str, ManifestEndpoint]
    specVersion: str = "v1alpha1"
    params: Optional[list[Param]] = None
    requiredApis: list[ManifestRequiredApi] = []
