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
Module for options that can be used to configure Firebase Cloud Functions
deployments.
"""
# pylint: disable=protected-access
import enum as _enum
import dataclasses as _dataclasses
import re as _re
import typing as _typing

import firebase_functions.private.manifest as _manifest
import firebase_functions.private.util as _util
from firebase_functions.params import SecretParam, Expression

USE_DEFAULT = _util.Sentinel(
    "Value used to reset an option to factory defaults")
"""Used to reset an option to its factory default."""


class VpcEgressSetting(str, _enum.Enum):
    """Valid settings for VPC egress."""

    PRIVATE_RANGES_ONLY = "PRIVATE_RANGES_ONLY"
    ALL_TRAFFIC = "ALL_TRAFFIC"


class IngressSetting(str, _enum.Enum):
    """What kind of traffic can access the Cloud Function."""

    ALLOW_ALL = "ALLOW_ALL"
    ALLOW_INTERNAL_ONLY = "ALLOW_INTERNAL_ONLY"
    ALLOW_INTERNAL_AND_GCLB = "ALLOW_INTERNAL_AND_GCLB"


@_dataclasses.dataclass(frozen=True)
class CorsOptions:
    """
    CORS options for Https functions.
    Internally this maps to Flask-Cors configuration see:
    https://flask-cors.corydolphin.com/en/latest/configuration.html
    """

    cors_origins: str | list[str] | _re.Pattern | None = None
    """
    The origin(s) to allow requests from. An origin configured here that matches the value of
    the Origin header in a preflight OPTIONS request is returned as the value of the
    Access-Control-Allow-Origin response header.
    """

    cors_methods: str | list[str] | None = None
    """
    The method(s) which the allowed origins are allowed to access.
    These are included in the Access-Control-Allow-Methods response headers
    to the preflight OPTIONS requests.
    """


class MemoryOption(int, _enum.Enum):
    """
    Available memory options supported by Cloud Functions.
    """

    MB_128 = 128
    MB_256 = 256
    MB_512 = 512
    GB_1 = 1 << 10
    GB_2 = 2 << 10
    GB_4 = 4 << 10
    GB_8 = 8 << 10
    GB_16 = 16 << 10
    GB_32 = 32 << 10


class SupportedRegion(str, _enum.Enum):
    """
    All regions supported by Cloud Functions v2.
    """

    ASIA_NORTHEAST1 = "asia-northeast1"
    EUROPE_NORTH1 = "europe-north1"
    EUROPE_WEST1 = "europe-west1"
    EUROPE_WEST4 = "europe-west4"
    US_CENTRAL1 = "us-central1"
    US_EAST1 = "us-east1"
    US_WEST1 = "us-west1"


class RateLimits():
    """
    How congestion control should be applied to the function.
    """
    max_concurrent_dispaches: int | Expression[
        int] | _util.Sentinel | None = None
    """
    The maximum number of requests that can be outstanding at a time.
    If left unspecified, will default to 1000.
    """

    max_dispatches_per_second: int | Expression[
        int] | _util.Sentinel | None = None
    """
    The maximum number of requests that can be invoked per second.
    If left unspecified, will default to 500.
    """


@_dataclasses.dataclass(frozen=True, kw_only=True)
class RuntimeOptions:
    """
    RuntimeOptions are options that can be set on any function or globally.
    Internal use only.
    """

    region: SupportedRegion | str | list[SupportedRegion | str] | None = None
    """
    Region where functions should be deployed.
    HTTP functions can specify more than one region.
    """

    memory: int | MemoryOption | Expression[int] | _util.Sentinel | None = None
    """
    Amount of memory to allocate to a function.
    A value of USE_DEFAULT restores the defaults of 256MB.
    """

    timeout_sec: int | Expression[int] | _util.Sentinel | None = None
    """
    Timeout for the function in sections, possible values are 0 to 540.
    HTTPS functions can specify a higher timeout.
    A value of USE_DEFAULT restores the default of 60s
    The minimum timeout for a gen 2 function is 1s. The maximum timeout for a
    function depends on the type of function: Event handling functions have a
    maximum timeout of 540s (9 minutes). HTTPS and callable functions have a
    maximum timeout of 36,00s (1 hour). Task queue functions have a maximum
    timeout of 1,800s (30 minutes)
    """

    min_instances: int | Expression[int] | _util.Sentinel | None = None
    """
    Min number of actual instances to be running at a given time.
    Instances will be billed for memory allocation and 10% of CPU allocation
    while idle.
    A value of USE_DEFAULT restores the default min instances.
    """

    max_instances: int | Expression[int] | _util.Sentinel | None = None
    """
    Max number of instances to be running in parallel.
    A value of USE_DEFAULT restores the default max instances.
    """

    concurrency: int | Expression[int] | _util.Sentinel | None = None
    """
    Number of requests a function can serve at once.
    Can only be applied to functions running on Cloud Functions v2.
    A value of USE_DEFAULT restores the default concurrency (80 when CPU >= 1, 1 otherwise).
    Concurrency cannot be set to any value other than 1 if `cpu` is less than 1.
    The maximum value for concurrency is 1,000.
    """

    cpu: int | _typing.Literal["gcf_gen1"] | _util.Sentinel | None = None
    """
    Fractional number of CPUs to allocate to a function.
    Defaults to 1 for functions with <= 2GB RAM and increases for larger memory sizes.
    This is different from the defaults when using the gcloud utility and is different from
    the fixed amount assigned in Google Cloud Functions generation 1.
    To revert to the CPU amounts used in gcloud or in Cloud Functions generation 1, set this
    to the value "gcf_gen1"
    """

    vpc_connector: str | None = None
    """
    Connect cloud function to specified VPC connector.
    A value of USE_DEFAULT removes the VPC connector.
    """

    vpc_connector_egress_settings: VpcEgressSetting | None = None
    """
    Egress settings for VPC connector.
    A value of USE_DEFAULT turns off VPC connector egress settings.
    """

    service_account: str | _util.Sentinel | None = None
    """
    Specific service account for the function to run as.
    A value of USE_DEFAULT restores the default service account.
    """

    ingress: IngressSetting | _util.Sentinel | None = None
    """
    Ingress settings which control where this function can be called from.
    A value of USE_DEFAULT turns off ingress settings.
    """

    labels: dict[str, str] | None = None
    """
    User labels to set on the function.
    """

    secrets: list[str] | list[SecretParam] | _util.Sentinel | None = None
    """
    Secrets to bind to a function.
    """

    def _asdict_with_global_options(self) -> dict:
        """
        Returns the provider options merged with globally defined options.
        """
        # We don't use dataclasses.asdict with a custom dict factory since
        # it internally converts dataclasses to dicts automatically but
        # we don't want that since we want to represent certain dataclasses
        # (such as params) differently (not as a dict) when converting to
        # a manifest representation.
        provider_options = _manifest._dict_to_spec(self.__dict__)
        global_options = _manifest._dict_to_spec(_GLOBAL_OPTIONS.__dict__)
        merged_options: dict = {**global_options, **provider_options}

        if self.labels is not None and _GLOBAL_OPTIONS.labels is not None:
            merged_options["labels"] = {**_GLOBAL_OPTIONS.labels, **self.labels}
        if "labels" not in merged_options:
            merged_options["labels"] = {}

        # _util.Sentinel values are converted to `None` in ManifestEndpoint generation
        # after other None values are removed - so as to keep them in the generated
        # YAML output as 'null' values.
        return merged_options

    def _endpoint(self, **kwargs) -> _manifest.ManifestEndpoint:
        assert kwargs["func_name"] is not None
        options_dict = self._asdict_with_global_options()
        options = self.__class__(**options_dict)

        secret_envs: list[
            _manifest.SecretEnvironmentVariable] | _util.Sentinel = []
        if options.secrets is not None:
            if isinstance(options.secrets, list):

                def convert_secret(
                        secret) -> _manifest.SecretEnvironmentVariable:
                    secret_value = secret
                    if isinstance(secret, SecretParam):
                        secret_value = secret.name
                    return {"key": secret_value}

                secret_envs = list(
                    map(convert_secret, _typing.cast(list, options.secrets)))
            elif options.secrets is _util.Sentinel:
                secret_envs = _typing.cast(_util.Sentinel, options.secrets)

        region: list[str] | None = None
        if isinstance(options.region, list):
            region = _typing.cast(list, options.region)
        elif options.region is not None:
            region = [_typing.cast(str, options.region)]

        vpc: _manifest.VpcSettings | None = None
        if options.vpc_connector is not None:
            vpc = ({
                "connector": options.vpc_connector,
                "egressSettings": options.vpc_connector_egress_settings.value
            } if options.vpc_connector_egress_settings is not None else {
                "connector": options.vpc_connector
            })

        endpoint = _manifest.ManifestEndpoint(
            entryPoint=kwargs["func_name"],
            region=region,
            availableMemoryMb=options.memory,
            labels=options.labels,
            maxInstances=options.max_instances,
            minInstances=options.min_instances,
            concurrency=options.concurrency,
            serviceAccountEmail=options.service_account,
            timeoutSeconds=options.timeout_sec,
            cpu=options.cpu,
            ingressSettings=options.ingress,
            secretEnvironmentVariables=secret_envs,
            vpc=vpc,
        )

        return endpoint


@_dataclasses.dataclass(frozen=True, kw_only=True)
class TaskQueueOptions(RuntimeOptions):
    """
    Options specific to Tasks function types.
    Internal use only.
    """

    retry_limit: _typing.Optional[_manifest.RetryConfig] = None
    """
    How a task should be retried in the event of a non-2xx return.
    """

    invoker: _typing.Optional[str | list[str] |
                              _typing.Literal["private"]] = None
    """
    Who can enqueue tasks for this function.

    Note:
        If left unspecified, only service accounts which have
        `roles/cloudtasks.enqueuer` and `roles/cloudfunctions.invoker`
        will have permissions.
    """

    omit: _typing.Optional[bool | Expression[bool]] = None
    """
    If true, do not deploy or emulate this function.
    """

    def _endpoint(
        self,
        **kwargs,
    ) -> _manifest.ManifestEndpoint:
        kwargs_merged = {
            **_dataclasses.asdict(super()._endpoint(**kwargs)),
            "taskQueueTrigger":
                _manifest.TaskQueueTrigger(),
        }
        return _manifest.ManifestEndpoint(
            **_typing.cast(_typing.Dict, kwargs_merged))


@_dataclasses.dataclass(frozen=True, kw_only=True)
class PubSubOptions(RuntimeOptions):
    """
    Options specific to Pub/Sub function types.
    Internal use only.
    """

    retry: _typing.Optional[bool] = None
    """
    Whether failed executions should be delivered again.
    """

    topic: str
    """
    The Pub/Sub topic to watch for message events.
    """

    def _endpoint(
        self,
        **kwargs,
    ) -> _manifest.ManifestEndpoint:
        event_filters: _typing.Any = {
            "topic": self.topic,
        }
        event_trigger = _manifest.EventTrigger(
            eventType="google.cloud.pubsub.topic.v1.messagePublished",
            retry=False,
            eventFilters=event_filters,
        )

        kwargs_merged = {
            **_dataclasses.asdict(super()._endpoint(**kwargs)),
            "eventTrigger":
                event_trigger,
        }
        return _manifest.ManifestEndpoint(
            **_typing.cast(_typing.Dict, kwargs_merged))


@_dataclasses.dataclass(frozen=True, kw_only=True)
class StorageOptions(RuntimeOptions):
    """
    Options specific to Storage function types.
    Internal use only.
    """

    bucket: _typing.Optional[str] = None
    """
    The name of the bucket to watch for Storage events.
    """

    def _endpoint(
        self,
        **kwargs,
    ) -> _manifest.ManifestEndpoint:
        assert kwargs["event_type"] is not None
        # TODO get bucket from admin sdk if no bucket set
        event_filters: _typing.Any = {
            "bucket": self.bucket,
        }
        event_trigger = _manifest.EventTrigger(
            eventType=kwargs["event_type"],
            retry=False,
            eventFilters=event_filters,
        )

        kwargs_merged = {
            **_dataclasses.asdict(super()._endpoint(**kwargs)),
            "eventTrigger":
                event_trigger,
        }
        return _manifest.ManifestEndpoint(
            **_typing.cast(_typing.Dict, kwargs_merged))


@_dataclasses.dataclass(frozen=True, kw_only=True)
class DatabaseOptions(RuntimeOptions):
    """
    Options specific to Database function types.
    Internal use only.
    """

    reference: str
    """
    Specify the handler to trigger on a database reference(s).
    This value can either be a single reference or a pattern.
    Examples: '/foo/bar', '/foo/{bar}'
    """

    instance: _typing.Optional[str] = None
    """
    Specify the handler to trigger on a database instance(s).
    If present, this value can either be a single instance or a pattern.
    Examples: 'my-instance-1', 'my-instance-*'
    Note: The capture syntax cannot be used for 'instance'.
    """

    def _endpoint(
        self,
        **kwargs,
    ) -> _manifest.ManifestEndpoint:
        assert kwargs["event_type"] is not None
        event_filter_instance = self.instance if self.instance is not None else "*"
        event_filters: _typing.Any = {}
        event_filters_path_patterns: _typing.Any = {
            # Note: Eventarc always treats ref as a path pattern
            "ref": self.reference.strip("/"),
        }
        if "*" in event_filter_instance:
            event_filters_path_patterns["instance"] = event_filter_instance
        else:
            event_filters["instance"] = event_filter_instance

        event_trigger = _manifest.EventTrigger(
            eventType=kwargs["event_type"],
            retry=False,
            eventFilters=event_filters,
            eventFilterPathPatterns=event_filters_path_patterns,
        )

        kwargs_merged = {
            **_dataclasses.asdict(super()._endpoint(**kwargs)),
            "eventTrigger":
                event_trigger,
        }
        return _manifest.ManifestEndpoint(
            **_typing.cast(_typing.Dict, kwargs_merged))


@_dataclasses.dataclass(frozen=True, kw_only=True)
class HttpsOptions(RuntimeOptions):
    """
    Options specific to Http function types.
    Internal use only.
    """

    invoker: str | list[str] | _typing.Literal["public",
                                               "private"] | None = None
    """
    Invoker to set access control on https functions.
    """

    cors: _typing.Optional[CorsOptions] = None
    """
    Optionally set CORS options for Https functions.
    """

    def _asdict_with_global_options(self) -> dict:
        """
        Returns the Https options merged with globally defined options and
        client only options like "cors" removed.
        """
        merged_options = super()._asdict_with_global_options()
        # "cors" is only used locally by the functions framework
        # and is not used in the manifest.
        if "cors" in merged_options:
            del merged_options["cors"]
        return merged_options

    def _endpoint(
        self,
        **kwargs,
    ) -> _manifest.ManifestEndpoint:
        kwargs_merged: dict[str, _typing.Any] = {
            **_dataclasses.asdict(super()._endpoint(**kwargs)),
        }

        if "callable" in kwargs and kwargs["callable"] is True:
            labels = _typing.cast(dict[str, str], kwargs_merged["labels"])
            labels["deployment-callable"] = "true"
            kwargs_merged["labels"] = labels
            kwargs_merged["callableTrigger"] = _manifest.CallableTrigger()
        else:
            https_trigger = _manifest.HttpsTrigger()
            if self.invoker is not None:
                invoker = self.invoker
                if isinstance(invoker, str):
                    invoker = [invoker]
                assert len(
                    invoker
                ) > 1, "HttpsOptions: Invalid option for invoker - must be a non-empty list."
                assert "" not in invoker, (
                    "HttpsOptions: Invalid option for invoker - must be a non-empty string."
                )
                if len(invoker) > 1:
                    assert "private" not in invoker and "public" not in invoker, (
                        # pylint: disable=line-too-long
                        "HttpsOptions: Cannot have 'public' or 'private' in a list of service accounts."
                    )
                https_trigger["invoker"] = invoker
            kwargs_merged["httpsTrigger"] = https_trigger

        return _manifest.ManifestEndpoint(
            **_typing.cast(_typing.Dict, kwargs_merged))


_GLOBAL_OPTIONS = RuntimeOptions()
"""The current default options for all functions. Internal use only."""


def set_global_options(
    *,
    region: SupportedRegion | str | list[SupportedRegion | str] | None = None,
    memory: int | MemoryOption | Expression[int] | _util.Sentinel | None = None,
    timeout_sec: int | Expression[int] | _util.Sentinel | None = None,
    min_instances: int | Expression[int] | _util.Sentinel | None = None,
    max_instances: int | Expression[int] | _util.Sentinel | None = None,
    concurrency: int | Expression[int] | _util.Sentinel | None = None,
    cpu: int | _typing.Literal["gcf_gen1"] | _util.Sentinel = "gcf_gen1",
    vpc_connector: str | None = None,
    vpc_connector_egress_settings: VpcEgressSetting | None = None,
    service_account: str | _util.Sentinel | None = None,
    ingress: IngressSetting | _util.Sentinel | None = None,
    labels: dict[str, str] | None = None,
    secrets: list[str] | list[SecretParam] | _util.Sentinel | None = None,
):
    """
    Sets default options for all functions.
    """
    global _GLOBAL_OPTIONS
    _GLOBAL_OPTIONS = RuntimeOptions(
        region=region,
        memory=memory,
        timeout_sec=timeout_sec,
        min_instances=min_instances,
        max_instances=max_instances,
        concurrency=concurrency,
        cpu=cpu,
        vpc_connector=vpc_connector,
        vpc_connector_egress_settings=vpc_connector_egress_settings,
        service_account=service_account,
        ingress=ingress,
        labels=labels,
        secrets=secrets,
    )
