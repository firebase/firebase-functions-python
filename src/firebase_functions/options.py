"""
Module for options that can be used to configure Cloud Functions
deployments.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Union

from firebase_functions.params import IntParam, SecretParam, StringParam, Expression


class Sentinel:
    """Class for USE_DEFAULT."""

    def __init__(self, description):
        self.description = description


USE_DEFAULT = Sentinel("Value used to reset an option to factory defaults")
""" Used to reset a function option to factory default. """


class VpcEgressSettings(str, Enum):
    """Valid settings for VPC egress."""

    PRIVATE_RANGES_ONLY = "PRIVATE_RANGES_ONLY"
    ALL_TRAFFIC = "ALL_TRAFFIC"


@dataclass(frozen=True)
class VpcOptions:
    """Configuration for a virtual private cloud (VPC).

    Attributes:
      connector: The ID of the connector to use. For maximal portability,
          prefer just an <id> instead of
          'projects/<project>/locations/<region>/connectors/<id>'.
      egress_setting: What kinds of outgoing connections can be established.
    """

    connector: str
    egress_settings: VpcEgressSettings


class IngressSettings(str, Enum):
    """What kind of traffic can access this Cloud Function."""

    ALLOW_ALL = "ALLOW_ALL"
    ALLOW_INTERNAL_ONLY = "ALLOW_INTERNAL_ONLY"
    ALLOW_INTERNAL_AND_GCLB = "ALLOW_INTERNAL_AND_GCLB"


class Memory(int, Enum):
    """Valid memory settings."""

    MB_256 = 256
    MB_512 = 512
    GB_1 = 1 << 10
    GB_2 = 2 << 10
    GB_4 = 4 << 10
    GB_8 = 8 << 10


@dataclass()
class GlobalOptions:
    """Options available for all function types in a codebase.

    Attributes:
        region: (str) Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
            Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
            time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
            Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
            Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
            the default compute service account.
    """

    instance: str | Expression[str] | Sentinel | None  = None
    allowed_origins: str | Expression[str] | Sentinel | None  = None
    allowed_methods: str | Expression[str] | Sentinel | None  = None
    region: str | Expression[str] | Sentinel | None  = None
    memory: int | Expression[int] | Sentinel | None  = None
    timeout_sec:  int | Expression[int] |  Sentinel  | None  = None
    min_instances:  int | Expression[int] |  Sentinel | None  = None
    max_instances:  int | Expression[int] |  Sentinel | None  = None
    concurrency: int | Expression[int] | Sentinel | None = None
    cpu: int | str | Sentinel = "gcf_gen1"
    vpc_connector_egress_settings: VpcEgressSettings | Sentinel | None = None
    vpc: VpcOptions | Sentinel | None = None
    ingress: IngressSettings | Sentinel | None = None
    service_account: str | Sentinel | None = None
    secrets: List[str] | SecretParam | Sentinel | None = None
    labels: Union[str, Expression[str], None] = None

    def metadata(self):
        return {
            "instance": self.instance,
            "allowed_origins": self.allowed_methods,
            "allowed_methods": self.allowed_methods,
            "region": self.region,
            "memory": self.memory,
            "timeout_sec": self.timeout_sec,
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "concurrency": self.concurrency,
            "cpu": self.cpu,
            "vpc_connector_egress_settings": self.vpc_connector_egress_settings,
            "vpc": self.vpc,
            "ingress": self.ingress,
            "service_account": self.service_account,
            "labels": self.labels,
        }


GLOBAL_OPTIONS = GlobalOptions()


class HttpsOptions(GlobalOptions):
    """Options available for all function types in a codebase.

    Attributes:
        region: (StringParam) Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
            Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
            time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
            Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
            Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
            the default compute service account.
    """

    allow_invalid_app_check_token: Optional[bool] = False

    invoker: Optional[list[str]] = None

    def __init__(
        self,
        max_instances=None,
        min_instances=None,
        timeout_sec=None,
        memory=None,
        region=None,
        allowed_origins=None,
        allowed_methods=None,
        service_account=None,
        vpc=None,
        vpc_connector_egress_settings=None,
        ingress=None,
        secrets=None,
        allow_invalid_app_check_token=False,
        invoker=None,
    ):
        super().__init__()
        self.max_instances = max_instances or GLOBAL_OPTIONS.max_instances
        self.allowed_methods = allowed_methods or GLOBAL_OPTIONS.allowed_methods
        self.allowed_origins = allowed_origins or GLOBAL_OPTIONS.allowed_origins
        self.ingress = ingress or GLOBAL_OPTIONS.ingress
        self.region = region or GLOBAL_OPTIONS.region
        self.memory = memory or GLOBAL_OPTIONS.memory
        self.timeout_sec = timeout_sec or GLOBAL_OPTIONS.timeout_sec
        self.min_instances = min_instances or GLOBAL_OPTIONS.min_instances
        self.vpc = vpc or GLOBAL_OPTIONS.vpc
        self.vpc_connector_egress_settings = (
            vpc_connector_egress_settings or
            GLOBAL_OPTIONS.vpc_connector_egress_settings)
        self.service_account = service_account or GLOBAL_OPTIONS.service_account
        self.secrets = secrets or GLOBAL_OPTIONS.secrets
        self.allow_invalid_app_check_token = allow_invalid_app_check_token
        invoker_list = []
        if invoker is not None:
            if isinstance(invoker, str):
                invoker_list.append(invoker)
            else:
                invoker_list.extend(invoker)
        self.invoker = invoker_list


class PubSubOptions(GlobalOptions):
    """Options available for all Pub/Sub function types in a codebase.

    Attributes:
        topic: The name of the Pub/Sub topic.
        region: (StringParam) Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
            Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
            time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
            Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
            Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
            the default compute service account.
    """

    topic: Optional[str] = None
    retry: Optional[bool] = None

    def __init__(
        self,
        max_instances=None,
        min_instances=None,
        timeout_sec=None,
        memory=None,
        region=None,
        allowed_origins=None,
        allowed_methods=None,
        service_account=None,
        vpc=None,
        vpc_connector_egress_settings=None,
        ingress=None,
        secrets=None,
        topic=None,
        retry=None,
    ):
        super().__init__()

        self.max_instances = max_instances or GLOBAL_OPTIONS.max_instances
        self.allowed_methods = allowed_methods or GLOBAL_OPTIONS.allowed_methods
        self.allowed_origins = allowed_origins or GLOBAL_OPTIONS.allowed_origins
        self.ingress = ingress or GLOBAL_OPTIONS.ingress
        self.region = region or GLOBAL_OPTIONS.region
        self.memory = memory or GLOBAL_OPTIONS.memory
        self.timeout_sec = timeout_sec or GLOBAL_OPTIONS.timeout_sec
        self.min_instances = min_instances or GLOBAL_OPTIONS.min_instances
        self.vpc = vpc or GLOBAL_OPTIONS.vpc
        self.vpc_connector_egress_settings = (
            vpc_connector_egress_settings or
            GLOBAL_OPTIONS.vpc_connector_egress_settings)
        self.service_account = service_account or GLOBAL_OPTIONS.service_account
        self.secrets = secrets or GLOBAL_OPTIONS.secrets
        self.topic = topic
        self.retry = retry or False


class ReferenceOptions(GlobalOptions):
    """Options available for all function types in a codebase.

    Attributes:
        region: (StringParam) Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
            Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
            time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
            Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
            Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
            the default compute service account.
    """

    def __init__(
        self,
        reference=None,
        instance=None,
        region=None,
        memory=None,
        timeout_sec=None,
        min_instances=None,
        max_instances=None,
        concurrency=None,
        cpu=None,
        vpc_connector_egress_settings=None,
        service_account=None,
        labels=None,
        allowed_origins=None,
        allowed_methods=None,
        vpc=None,
        ingress=None,
        secrets=None,
        retry=None,
    ):
        super().__init__()
        self.reference = reference or GLOBAL_OPTIONS.reference
        self.instance = instance or GLOBAL_OPTIONS.instance
        self.region = region or GLOBAL_OPTIONS.region
        self.memory = memory or GLOBAL_OPTIONS.memory
        self.timeout_sec = timeout_sec or GLOBAL_OPTIONS.timeout_sec
        self.max_instances = max_instances or GLOBAL_OPTIONS.max_instances
        self.min_instances = min_instances or GLOBAL_OPTIONS.min_instances
        self.concurrency = concurrency or GLOBAL_OPTIONS.concurrency
        self.cpu = cpu or GLOBAL_OPTIONS.cpu
        self.vpc_connector_egress_settings = (
            vpc_connector_egress_settings or
            GLOBAL_OPTIONS.vpc_connector_egress_settings)
        self.service_account = service_account or GLOBAL_OPTIONS.service_account
        self.labels = labels or GLOBAL_OPTIONS.labels
        self.allowed_methods = allowed_methods or GLOBAL_OPTIONS.allowed_methods
        self.allowed_origins = allowed_origins or GLOBAL_OPTIONS.allowed_origins
        self.ingress = ingress or GLOBAL_OPTIONS.ingress
        self.vpc = vpc or GLOBAL_OPTIONS.vpc
        self.secrets = secrets or GLOBAL_OPTIONS.secrets
        self.retry = retry or False


def set_global_options(
    *,
    instance: Union[None, str, Expression[str], Sentinel] = None,
    region: Optional[str] = None,
    memory: Union[None, int, Sentinel] = None,
    timeout_sec: Union[None, int, Sentinel] = None,
    min_instances: Union[None, int, Sentinel] = None,
    max_instances: Union[None, int, Sentinel] = None,
    concurrency: Union[None, int, Sentinel] = None,
    cpu: Union[None, int, str, Sentinel] = "gcf_gen1",
    vpc_connector_egress_settings: Union[None, VpcEgressSettings,
                                         Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, str, Sentinel] = None,
    labels: Union[str, Expression[str]] = None,
    allowed_origins: Union[StringParam, str,
                           None] = None,  # TODO should we add Sentinel?
    allowed_methods: Union[StringParam, str,
                           None] = None  # TODO should we add Sentinel?
):
    global GLOBAL_OPTIONS
    GLOBAL_OPTIONS = GlobalOptions(
        instance=instance,
        region=region,
        memory=memory,
        timeout_sec=timeout_sec,
        min_instances=min_instances,
        max_instances=max_instances,
        concurrency=concurrency,
        cpu=cpu,
        vpc_connector_egress_settings=vpc_connector_egress_settings,
        vpc=vpc,
        ingress=ingress,
        service_account=service_account,
        labels=labels,
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
    )
