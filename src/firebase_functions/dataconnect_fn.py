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
Module for Cloud Functions that are triggered by Firebase Data Connect.
"""

# pylint: disable=protected-access
import dataclasses as _dataclass
import functools as _functools
import typing as _typing

import cloudevents.http as _ce

import firebase_functions.core as _core
import firebase_functions.private.path_pattern as _path_pattern
import firebase_functions.private.util as _util
from firebase_functions.options import DataConnectOptions

_event_type_mutation_executed = "google.firebase.dataconnect.connector.v1.mutationExecuted"

AuthType = _typing.Literal["app_user", "admin", "unknown"]


@_dataclass.dataclass(frozen=True)
class Event(_core.CloudEvent[_core.T]):
    """
    A CloudEvent that contains MutationEventData.
    """

    location: str
    """
    The location of the database.
    """

    project: str
    """
    The project identifier.
    """

    params: dict[str, str]
    """
    A dict containing the values of the path patterns.
    Only named capture groups are populated - {key}, {key=*}, {key=**}
    """

    auth_type: AuthType
    """
    The type of principal that triggered the event.
    """

    auth_id: str
    """
    The unique identifier for the principal.
    """


@_dataclass.dataclass(frozen=True)
class GraphqlErrorExtensions:
    """
    GraphqlErrorExtensions contains additional information of `GraphqlError`.
    """

    file: str
    """
    The source file name where the error occurred.
    Included only for `UpdateSchema` and `UpdateConnector`, it corresponds
    to `File.path` of the provided `Source`.
    """

    code: str
    """
    Maps to canonical gRPC codes.
    If not specified, it represents `Code.INTERNAL`.
    """

    debug_details: str
    """
    More detailed error message to assist debugging.
    It contains application business logic that are inappropriate to leak
    publicly.

    In the emulator, Data Connect API always includes it to assist local
    development and debugging.
    In the backend, ConnectorService always hides it.
    GraphqlService without impersonation always include it.
    GraphqlService with impersonation includes it only if explicitly opted-in
    with `include_debug_details` in `GraphqlRequestExtensions`.
    """


@_dataclass.dataclass(frozen=True)
class SourceLocation:
    """
    SourceLocation references a location in a GraphQL source.
    """

    line: int
    """
    Line number starting at 1.
    """

    column: int
    """
    Column number starting at 1.
    """


@_dataclass.dataclass(frozen=True)
class GraphQLError:
    """
    An error that occurred during the execution of a GraphQL request.
    """

    message: str
    """
    A string describing the error.
    """

    locations: list[dict[str, int]] | None = None
    """
    The source locations where the error occurred.
    Locations should help developers and toolings identify the source of error
    quickly.

    Included in admin endpoints (`ExecuteGraphql`, `ExecuteGraphqlRead`,
    `UpdateSchema` and `UpdateConnector`) to reference the provided GraphQL
    GQL document.

    Omitted in `ExecuteMutation` and `ExecuteQuery` since the caller shouldn't
    have access access the underlying GQL source.
    """

    path: list[str | int] | None = None
    """
    The result field which could not be populated due to error.

    Clients can use path to identify whether a null result is intentional or
    caused by a runtime error.
    It should be a list of string or index from the root of GraphQL query
    document.
    """

    extensions: GraphqlErrorExtensions | None = None


@_dataclass.dataclass(frozen=True)
class Mutation:
    """
    An object within Firebase Data Connect.
    """

    data: _typing.Any
    """
    The result of the execution of the requested operation.
    If an error was raised before execution begins, the data entry should not
    be present in the result. (a request error:
    https://spec.graphql.org/draft/#sec-Errors.Request-Errors) If an error was
    raised during the execution that prevented a valid response, the data entry
    in the response should be null. (a field error:
    https://spec.graphql.org/draft/#sec-Errors.Error-Result-Format)
    """

    variables: _typing.Any
    """
    Values for GraphQL variables provided in this request.
    """

    errors: list[GraphQLError] | None = None
    """
    Errors of this response.
    If the data entry in the response is not present, the errors entry must be
    present.
    It conforms to https://spec.graphql.org/draft/#sec-Errors.
    """


@_dataclass.dataclass(frozen=True)
class MutationEventData:
    """
    The data within all Mutation events.
    """

    payload: Mutation


_E1 = Event[MutationEventData]
_C1 = _typing.Callable[[_E1], None]


def _dataconnect_endpoint_handler(
    func: _C1,
    event_type: str,
    service_pattern: _path_pattern.PathPattern | None,
    connector_pattern: _path_pattern.PathPattern | None,
    operation_pattern: _path_pattern.PathPattern | None,
    raw: _ce.CloudEvent,
) -> None:
    # Currently, only mutationExecuted is supported
    if event_type != _event_type_mutation_executed:
        raise NotImplementedError(
            f"Unsupported event type: {event_type}. Only {_event_type_mutation_executed} is currently supported."
        )

    event_attributes = raw._get_attributes()
    event_data: _typing.Any = raw.get_data()

    dataconnect_event_data = event_data

    event_service = event_attributes["service"]
    event_connector = event_attributes["connector"]
    event_operation = event_attributes["operation"]
    params: dict[str, str] = {}

    if service_pattern:
        params = {**params, **service_pattern.extract_matches(event_service)}
    if connector_pattern:
        params = {**params, **connector_pattern.extract_matches(event_connector)}
    if operation_pattern:
        params = {**params, **operation_pattern.extract_matches(event_operation)}

    event_auth_type = event_attributes["authtype"]
    event_auth_id = event_attributes["authid"]
    event_time = _util.timestamp_conversion(event_attributes["time"])

    dataconnect_event = Event(
        specversion=event_attributes["specversion"],
        id=event_attributes["id"],
        source=event_attributes["source"],
        type=event_attributes["type"],
        time=event_time,
        subject=event_attributes.get("subject"),
        location=event_attributes["location"],
        project=event_attributes["project"],
        params=params,
        data=dataconnect_event_data,
        auth_type=event_auth_type,
        auth_id=event_auth_id,
    )
    _core._with_init(func)(dataconnect_event)


@_util.copy_func_kwargs(DataConnectOptions)
def on_mutation_executed(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler that triggers when a mutation is executed in Firebase Data Connect.

    Example:

    .. code-block:: python

      @on_mutation_executed(
        service = "service-id",
        connector = "connector-id",
        operation = "mutation-name"
      )
      def mutation_executed_handler(event: Event[MutationEventData]):
        pass

    :param \\*\\*kwargs: DataConnect options.
    :type \\*\\*kwargs: as :exc:`firebase_functions.options.DataConnectOptions`
    :rtype: :exc:`typing.Callable`
            \\[ \\[ :exc:`firebase_functions.dataconnect_fn.Event` \\[
            :exc:`object` \\] \\], `None` \\]
            A function that takes a DataConnect event and returns ``None``.
    """
    options = DataConnectOptions(**kwargs)

    def on_mutation_executed_inner_decorator(func: _C1):
        service_pattern = _path_pattern.PathPattern(options.service) if options.service else None
        connector_pattern = (
            _path_pattern.PathPattern(options.connector) if options.connector else None
        )
        operation_pattern = (
            _path_pattern.PathPattern(options.operation) if options.operation else None
        )

        @_functools.wraps(func)
        def on_mutation_executed_wrapped(raw: _ce.CloudEvent):
            return _dataconnect_endpoint_handler(
                func,
                _event_type_mutation_executed,
                service_pattern,
                connector_pattern,
                operation_pattern,
                raw,
            )

        _util.set_func_endpoint_attr(
            on_mutation_executed_wrapped,
            options._endpoint(
                event_type=_event_type_mutation_executed,
                func_name=func.__name__,
                service_pattern=service_pattern,
                connector_pattern=connector_pattern,
                operation_pattern=operation_pattern,
            ),
        )
        return on_mutation_executed_wrapped

    return on_mutation_executed_inner_decorator
