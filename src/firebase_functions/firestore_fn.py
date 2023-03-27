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
Module for Cloud Functions that are triggered by Firestore.
"""
# pylint: disable=protected-access
import dataclasses as _dataclass
import functools as _functools
import typing as _typing
import datetime as _dt
import google.events.cloud.firestore as _firestore
import firebase_functions.private.util as _util
import firebase_functions.private.path_pattern as _path_pattern
import firebase_functions.core as _core
import cloudevents.http as _ce

from firebase_functions.options import FirestoreOptions
from firebase_functions.core import Change

_event_type_written = "google.cloud.firestore.document.v1.written"
_event_type_created = "google.cloud.firestore.document.v1.created"
_event_type_updated = "google.cloud.firestore.document.v1.updated"
_event_type_deleted = "google.cloud.firestore.document.v1.deleted"


@_dataclass.dataclass(frozen=True)
class Event(_core.CloudEvent[_core.T]):
    """
    A CloudEvent that contains a DocumentSnapshot or a Change<DocumentSnapshot>.
    """

    location: str
    """
    The location of the database
    """

    project: str
    """
    The project identifier.
    """

    database: str
    """
    The Firestore database.
    """

    namespace: str
    """
    The Firestore namespace.
    """

    document: str
    """
    The document path.
    """

    params: dict[str, str]
    """
    An dict containing the values of the path patterns.
    Only named capture groups are populated - {key}, {key=*}, {key=**}
    """


_E1 = Event[Change[_typing.Any | None]]
_E2 = Event[_typing.Any | None]
_C1 = _typing.Callable[[_E1], None]
_C2 = _typing.Callable[[_E2], None]


def _firestore_endpoint_handler(
    func: _C1 | _C2,
    event_type: str,
    document_pattern: _path_pattern.PathPattern,
    raw: _ce.CloudEvent,
) -> None:
    event_attributes = raw._get_attributes()
    event_data: _typing.Any = raw.get_data()
    firestore_event_data: _firestore.DocumentEventData

    # TODO also check event_attributes['datacontenttype'] includes
    # 'application/json' || 'application/protobuf'
    if isinstance(event_data, dict):
        # TODO event_data may need to be a JSON string
        firestore_event_data = _firestore.DocumentEventData.from_json(
            event_data)
    elif isinstance(event_data, bytes):
        firestore_event_data = _firestore.DocumentEventData.deserialize(
            event_data)
    else:
        # Throw an error if the data is not a string or bytes.
        raise TypeError("Firestore CloudEvent data must be a string or bytes")

    if event_type == _event_type_deleted:
        firestore_event_data = firestore_event_data.value
    if event_type == _event_type_created:
        firestore_event_data = firestore_event_data.value
    if event_type in (_event_type_written, _event_type_updated):
        before = firestore_event_data.old_value
        after = firestore_event_data.value
        firestore_event_data = Change(
            before=before,
            after=after,
        )
    event_location = event_attributes["location"]
    event_project = event_attributes["project"]
    event_namespace = event_attributes["namespace"]
    event_database = event_attributes["database"]
    event_document = event_attributes["document"]
    params: dict[str, str] = {
        **document_pattern.extract_matches(event_document),
    }
    database_event = Event(
        project=event_project,
        namespace=event_namespace,
        database=event_database,
        location=event_location,
        document=event_document,
        specversion=event_attributes["specversion"],
        id=event_attributes["id"],
        source=event_attributes["source"],
        type=event_attributes["type"],
        time=_dt.datetime.strptime(
            event_attributes["time"],
            "%Y-%m-%dT%H:%M:%S.%f%z",
        ),
        data=firestore_event_data,
        subject=event_attributes["subject"],
        params=params,
    )
    func(database_event)


@_util.copy_func_kwargs(FirestoreOptions)
def on_document_written(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler which triggers when a document is created, updated, or deleted in Firestore.

    Example:

    .. code-block:: python

      @on_document_written(document="*")
      def example(event: Event[Change[object]]) -> None:
          pass

    :param \\*\\*kwargs: Firestore options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.FirestoreOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.firestore_fn.Event` \\[
            :exc:`firebase_functions.db.Change` \\] \\], `None` \\]
            A function that takes a Firestore Event and returns None.
    """
    options = FirestoreOptions(**kwargs)

    def on_document_written_inner_decorator(func: _C1):
        document_pattern = _path_pattern.PathPattern(options.document)

        @_functools.wraps(func)
        def on_document_written_wrapped(raw: _ce.CloudEvent):
            return _firestore_endpoint_handler(
                func,
                _event_type_written,
                document_pattern,
                raw,
            )

        _util.set_func_endpoint_attr(
            on_document_written_wrapped,
            options._endpoint(
                event_type=_event_type_written,
                func_name=func.__name__,
                document_pattern=document_pattern,
            ),
        )
        return on_document_written_wrapped

    return on_document_written_inner_decorator


@_util.copy_func_kwargs(FirestoreOptions)
def on_document_updated(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler which triggers when a document is updated in Firestore.

    Example:

    .. code-block:: python

      @on_document_updated(document="*")
      def example(event: Event[Change[object]]) -> None:
          pass

    :param \\*\\*kwargs: Firestore options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.FirestoreOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.firestore_fn.Event` \\[
            :exc:`firebase_functions.db.Change` \\] \\], `None` \\]
            A function that takes a Firestore Event and returns None.
    """
    options = FirestoreOptions(**kwargs)

    def on_document_updated_inner_decorator(func: _C1):
        document_pattern = _path_pattern.PathPattern(options.document)

        @_functools.wraps(func)
        def on_document_updated_wrapped(raw: _ce.CloudEvent):
            return _firestore_endpoint_handler(
                func,
                _event_type_updated,
                document_pattern,
                raw,
            )

        _util.set_func_endpoint_attr(
            on_document_updated_wrapped,
            options._endpoint(
                event_type=_event_type_updated,
                func_name=func.__name__,
                document_pattern=document_pattern,
            ),
        )
        return on_document_updated_wrapped

    return on_document_updated_inner_decorator


@_util.copy_func_kwargs(FirestoreOptions)
def on_document_created(**kwargs) -> _typing.Callable[[_C2], _C2]:
    """
    Event handler which triggers when a document is created in Firestore.

    Example:

    .. code-block:: python

        @on_document_created(document="*")
        def example(event: Event[object]):
          pass

    :param \\*\\*kwargs: Firestore options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.FirestoreOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.firestore_fn.Event` \\[
            :exc:`object` \\] \\], `None` \\]
            A function that takes a Firestore Event and returns None.
    """
    options = FirestoreOptions(**kwargs)

    def on_document_created_inner_decorator(func: _C2):
        document_pattern = _path_pattern.PathPattern(options.document)

        @_functools.wraps(func)
        def on_document_created_wrapped(raw: _ce.CloudEvent):
            return _firestore_endpoint_handler(
                func,
                _event_type_created,
                document_pattern,
                raw,
            )

        _util.set_func_endpoint_attr(
            on_document_created_wrapped,
            options._endpoint(
                event_type=_event_type_created,
                func_name=func.__name__,
                document_pattern=document_pattern,
            ),
        )
        return on_document_created_wrapped

    return on_document_created_inner_decorator


@_util.copy_func_kwargs(FirestoreOptions)
def on_document_deleted(**kwargs) -> _typing.Callable[[_C2], _C2]:
    """
    Event handler which triggers when a document is deleted in Firestore.

    Example:

    .. code-block:: python

      @on_document_deleted(document="*")
      def example(event: Event[object]) -> None:
          pass

    :param \\*\\*kwargs: Firestore options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.FirestoreOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.firestore_fn.Event` \\[
            :exc:`object` \\] \\], `None` \\]
            A function that takes a Firestore Event and returns None.
    """
    options = FirestoreOptions(**kwargs)

    def on_document_deleted_inner_decorator(func: _C2):
        document_pattern = _path_pattern.PathPattern(options.document)

        @_functools.wraps(func)
        def on_document_deleted_wrapped(raw: _ce.CloudEvent):
            return _firestore_endpoint_handler(
                func,
                _event_type_deleted,
                document_pattern,
                raw,
            )

        _util.set_func_endpoint_attr(
            on_document_deleted_wrapped,
            options._endpoint(
                event_type=_event_type_deleted,
                func_name=func.__name__,
                document_pattern=document_pattern,
            ),
        )
        return on_document_deleted_wrapped

    return on_document_deleted_inner_decorator
