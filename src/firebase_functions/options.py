"""
Module for options that can be used to configure Firebase Cloud Functions
deployments.
"""

import enum as _enum
import dataclasses as _dataclasses
import re as _re
import typing as _typing

from firebase_functions.params import SecretParam, Expression


class _Sentinel:
    """Internal class for USE_DEFAULT."""

    def __init__(self, description):
        self.description = description


USE_DEFAULT = _Sentinel("Value used to reset an option to factory defaults")
"""Used to reset an option to its factory default."""


class VpcEgressSettings(str, _enum.Enum):
    """Valid settings for VPC egress."""

    PRIVATE_RANGES_ONLY = "PRIVATE_RANGES_ONLY"
    ALL_TRAFFIC = "ALL_TRAFFIC"


class IngressSettings(str, _enum.Enum):
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


class Memory(int, _enum.Enum):
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


@_dataclasses.dataclass(frozen=True)
class _CommonOptions:
    """
    _CommonOptions are options that can be set on any function or globally.
    Internal use only.
    """

    region: SupportedRegion | str | _Sentinel | None = None
    """
    Region where functions should be deployed.
    HTTP functions can override and specify more than one region.
    """

    memory: int | Memory | Expression[int] | _Sentinel | None = None
    """
    Amount of memory to allocate to a function.
    A value of USE_DEFAULT restores the defaults of 256MB.
    """

    timeout_sec: int | Expression[int] | _Sentinel | None = None
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

    min_instances: int | Expression[int] | _Sentinel | None = None
    """
    Min number of actual instances to be running at a given time.
    Instances will be billed for memory allocation and 10% of CPU allocation
    while idle.
    A value of USE_DEFAULT restores the default min instances.
    """

    max_instances: int | Expression[int] | _Sentinel | None = None
    """
    Max number of instances to be running in parallel.
    A value of USE_DEFAULT restores the default max instances.
    """

    concurrency: int | Expression[int] | _Sentinel | None = None
    """
    Number of requests a function can serve at once.
    Can only be applied to functions running on Cloud Functions v2.
    A value of USE_DEFAULT restores the default concurrency (80 when CPU >= 1, 1 otherwise).
    Concurrency cannot be set to any value other than 1 if `cpu` is less than 1.
    The maximum value for concurrency is 1,000.
    """

    cpu: int | _typing.Literal["gcf_gen1"] | _Sentinel | None = None
    """
    Fractional number of CPUs to allocate to a function.
    Defaults to 1 for functions with <= 2GB RAM and increases for larger memory sizes.
    This is different from the defaults when using the gcloud utility and is different from
    the fixed amount assigned in Google Cloud Functions generation 1.
    To revert to the CPU amounts used in gcloud or in Cloud Functions generation 1, set this
    to the value "gcf_gen1"
    """

    vpc_connector: str | _Sentinel | None = None
    """
    Connect cloud function to specified VPC connector.
    A value of USE_DEFAULT removes the VPC connector.
    """

    vpc_connector_egress_settings: VpcEgressSettings | _Sentinel | None = None
    """
    Egress settings for VPC connector.
    A value of USE_DEFAULT turns off VPC connector egress settings.
    """

    service_account: str | _Sentinel | None = None
    """
    Specific service account for the function to run as.
    A value of USE_DEFAULT restores the default service account.
    """

    ingress: IngressSettings | _Sentinel | None = None
    """
    Ingress settings which control where this function can be called from.
    A value of USE_DEFAULT turns off ingress settings.
    """

    labels: dict[str, str] | None = None
    """
    User labels to set on the function.
    """

    secrets: list[str] | list[SecretParam] | _Sentinel | None = None
    """
    Secrets to bind to a function.
    """


_GLOBAL_OPTIONS = _CommonOptions()
"""The current default options for all functions. Internal use only."""


@_dataclasses.dataclass(frozen=True)
class _ProviderOptions:
    """
    Base class for provider specific options.
    """

    # We don't inherit _CommonOptions since some options can be overloaded
    # with new types which will break inheritance.
    options: _CommonOptions
    """
    Base options.
    """

    def asdict_with_global_options(self) -> dict:
        """
        Returns the provider options merged with globally defined options.
        """
        provider_options = _dataclasses.asdict(self)
        # Copy base options to root of provider options.
        provider_options = {**provider_options["options"], **provider_options}
        del provider_options["options"]
        global_options = _dataclasses.asdict(_GLOBAL_OPTIONS)
        merged_options: dict = {**global_options, **provider_options}
        # None values in the providers options should fallback to
        # global options.
        for key in provider_options:
            if provider_options[key] is None and key in global_options:
                merged_options[key] = global_options[key]
        # None values are automatically stripped out in ManifestEndpoint generation.

        # _Sentinel values are converted to `None` in ManifestEndpoint generation
        # after other None values are removed - so as to keep them in the generated
        # YAML output as 'null' values.
        return merged_options


@_dataclasses.dataclass(frozen=True)
class _PubSubOptions(_ProviderOptions):
    """
    Options specific to Pub/Sub function types.
    Internal use only.
    """

    topic: str
    """
    The Pub/Sub topic to watch for message events.
    """

    retry: _typing.Optional[bool] = None
    """
    Whether failed executions should be delivered again.
    """


@_dataclasses.dataclass(frozen=True)
class _HttpsOptions(_ProviderOptions):
    """
    Options specific to Http function types.
    Internal use only.
    """

    region: SupportedRegion | str | list[SupportedRegion | str] | None = None
    """
    Region(s) where functions should be deployed.
    HTTP functions can override and specify more than one region unlike others function types.
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

    def asdict_with_global_options(self) -> dict:
        """
        Returns the Https options merged with globally defined options and
        client only options like "cors" removed.
        """
        merged_options = super().asdict_with_global_options()
        del merged_options["cors"]
        return merged_options


def set_global_options(
    *,
    region: SupportedRegion | str | _Sentinel | None = None,
    memory: int | Memory | Expression[int] | _Sentinel | None = None,
    timeout_sec: int | Expression[int] | _Sentinel | None = None,
    min_instances: int | Expression[int] | _Sentinel | None = None,
    max_instances: int | Expression[int] | _Sentinel | None = None,
    concurrency: int | Expression[int] | _Sentinel | None = None,
    cpu: int | _typing.Literal["gcf_gen1"] | _Sentinel = "gcf_gen1",
    vpc_connector: str | _Sentinel | None = None,
    vpc_connector_egress_settings: VpcEgressSettings | _Sentinel | None = None,
    service_account: str | _Sentinel | None = None,
    ingress: IngressSettings | _Sentinel | None = None,
    labels: dict[str, str] | None = None,
    secrets: list[str] | list[SecretParam] | _Sentinel | None = None,
):
    """
    Sets default options for all functions.
    """
    global _GLOBAL_OPTIONS
    _GLOBAL_OPTIONS = _CommonOptions(
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
