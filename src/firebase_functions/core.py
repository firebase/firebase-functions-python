"""
Public code that is shared across modules.
"""
import dataclasses as _dataclass
import datetime as _datetime
import typing as _typing

T = _typing.TypeVar("T")


@_dataclass.dataclass(frozen=True)
class CloudEvent(_typing.Generic[T]):
    """
    A Cloud Event is the base of a cross-platform format for encoding a serverless event.
    More information can be found at https://github.com/cloudevents/spec
    """

    specversion: str
    """
    Version of the CloudEvents spec for this event.
    """

    id: str
    """
    A globally unique ID for this event.
    """

    source: str
    """
    The resource which published this event.
    """

    type: str
    """
    The type of event that this represents.
    """

    time: _datetime.datetime
    """
    When this event occurred.
    """

    data: T
    """
    Information about this specific event.
    """

    subject: str | None
    """
    The resource, provided by source, that this event relates to
    """


@_dataclass.dataclass(frozen=True)
class Change(_typing.Generic[T]):
    """
    * The Functions interface for events that change state, such as
    * Realtime Database `on_value_written`.
    """

    before: T
    """
    The state of data before the change.
    """

    after: T
    """
    The state of data after the change.
    """
