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
Cloud functions to handle events from Google Cloud Storage.
"""
# pylint: disable=protected-access
import dataclasses as _dataclasses
import datetime as _dt
import functools as _functools
import typing as _typing
import cloudevents.http as _ce

import firebase_functions.options as _options
import firebase_functions.private.util as _util
from firebase_functions.core import CloudEvent

_event_type_archived = "google.cloud.storage.object.v1.archived"
_event_type_finalized = "google.cloud.storage.object.v1.finalized"
_event_type_deleted = "google.cloud.storage.object.v1.deleted"
_event_type_metadata_updated = "google.cloud.storage.object.v1.metadataUpdated"


@_dataclasses.dataclass(frozen=True)
class CustomerEncryption:
    """
    Metadata of customer-supplied encryption key,
    if the object is encrypted by such a key.
    """

    encryption_algorithm: str
    """
    The encryption algorithm.
    """

    key_sha256: str
    """
    SHA256 hash value of the encryption key.
    """


@_dataclasses.dataclass(frozen=True)
class StorageObjectData:
    """
    An object within Google Cloud Storage.
    """

    bucket: str
    """
    The name of the bucket containing this object.
    """

    cache_control: _typing.Optional[str]
    """
    Cache-Control directive for the object data,
    matching [RFC 7234 §5.2]([https://tools.ietf.org/html/rfc7234#section-5.2"]).
    """

    component_count: _typing.Optional[int]
    """
    Number of underlying components that make up this object.
    Components are accumulated by compose operations.
    """

    content_disposition: _typing.Optional[str]
    """
    Content-Disposition of the object data,
    matching [RFC 6266]([https://tools.ietf.org/html/rfc6266"]).
    """

    content_encoding: _typing.Optional[str]
    """
    Content-Encoding of the object data,
    matching [RFC 7231 §3.1.2.2](https://tools.ietf.org/html/rfc7231#section-3.1.2.2)
    """

    content_language: _typing.Optional[str]
    """
    Content-Language of the object data,
    matching [RFC 7231 §3.1.3.2](https://tools.ietf.org/html/rfc7231#section-3.1.3.2)
    """

    content_type: _typing.Optional[str]
    """
    Content-Type of the object data, matching
    [RFC 7231 §3.1.1.5](https://tools.ietf.org/html/rfc7231#section-3.1.1.5)
    If an object is stored without a Content-Type, it is served as
    `application/octet-stream`.
    """

    crc32c: _typing.Optional[str]
    """
    CRC32c checksum. For more information about using the CRC32c checksum, see
    [Hashes and ETags: Best Practices](https://cloud.google.com/storage/docs/hashes-etags#_JSONAPI).
    """

    customer_encryption: _typing.Optional[CustomerEncryption]
    """
    Metadata of customer-supplied encryption key, if the object is encrypted by
    such a key.
    """

    etag: _typing.Optional[str]
    """
    HTTP 1.1 Entity tag for the object.
    """

    generation: int
    """
    The content generation of this object. Used for object versioning.
    """

    id: str
    """
    The ID of the object, including the bucket name, object name, and
    generation number.
    """

    kind: _typing.Optional[str]
    """
    The kind of item this is. For objects, this is always `storage#object`.
    """

    md5_hash: _typing.Optional[str]
    """
    MD5 hash of the data; encoded using base64.
    """

    media_link: _typing.Optional[str]
    """
    Media download link.
    """

    metadata: _typing.Optional[dict[str, str]]
    """
    User-provided metadata, in key/value pairs.
    """

    metageneration: int
    """
    The version of the metadata for this object at this generation.
    Used for preconditions and for detecting changes in metadata.
    A metageneration number is only meaningful in the context of a particular
    generation of a particular object.
    """

    name: str
    """
    The name of the object.
    """

    self_link: _typing.Optional[str]
    """
    The link to this object.
    """

    size: int
    """
    Content-Length of the data in bytes.
    """

    storage_class: str
    """
    Storage class of the object.
    """

    time_created: _typing.Optional[str]
    """
    The creation time of the object.
    """

    time_deleted: _typing.Optional[str]
    """
    The deletion time of the object.
    """

    time_storage_class_updated: _typing.Optional[str]
    """
    The time at which the object's storage class was last changed.
    """

    updated: _typing.Optional[str]
    """
    The modification time of the object metadata.
    """


_E1 = CloudEvent[StorageObjectData]
_C1 = _typing.Callable[[_E1], None]


def _message_handler(
    func: _C1,
    raw: _ce.CloudEvent,
) -> None:
    event_attributes = raw._get_attributes()
    event_data = raw._get_data()
    event_dict = {"data": event_data, **event_attributes}
    data = event_dict["data"]
    message_dict: dict = data["message"]

    time = _dt.datetime.strptime(
        event_dict["time"],
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    publish_time = _dt.datetime.strptime(
        message_dict["publish_time"],
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    # Convert the UTC string into a datetime object
    event_dict["time"] = time
    message_dict["publish_time"] = publish_time

    # Pop unnecessary keys from the message data
    # (we get these keys from the snake case alternatives that are provided)
    message_dict.pop("messageId", None)
    message_dict.pop("publishTime", None)

    message: StorageObjectData = StorageObjectData(
        # Required fields:
        bucket=message_dict["bucket"],
        generation=message_dict["generation"],
        id=message_dict["id"],
        metageneration=message_dict["metageneration"],
        name=message_dict["name"],
        size=message_dict["size"],
        storage_class=message_dict["storageClass"],
        # Optional fields:
        cache_control=message_dict.get("cacheControl"),
        component_count=message_dict.get("componentCount"),
        content_disposition=message_dict.get("contentDisposition"),
        content_encoding=message_dict.get("contentEncoding"),
        content_language=message_dict.get("contentLanguage"),
        content_type=message_dict.get("contentType"),
        crc32c=message_dict.get("crc32c"),
        etag=message_dict.get("etag"),
        kind=message_dict.get("kind"),
        md5_hash=message_dict.get("md5Hash"),
        media_link=message_dict.get("mediaLink"),
        metadata=message_dict.get("metadata"),
        self_link=message_dict.get("selfLink"),
        time_created=message_dict.get("timeCreated"),
        time_deleted=message_dict.get("timeDeleted"),
        time_storage_class_updated=message_dict.get("timeStorageClassUpdated"),
        updated=message_dict.get("updated"),
        # Custom type fields:
        customer_encryption=CustomerEncryption(
            encryption_algorithm=message_dict["customerEncryption"]
            ["encryptionAlgorithm"],
            key_sha256=message_dict["customerEncryption"]["keySha256"],
        ) if message_dict.get("customerEncryption") is not None else None,
    )

    event_dict["data"] = message

    event: CloudEvent[StorageObjectData] = CloudEvent(
        data=event_dict["data"],
        id=event_dict["id"],
        source=event_dict["source"],
        specversion=event_dict["specversion"],
        subject=event_dict["subject"] if "subject" in event_dict else None,
        time=event_dict["time"],
        type=event_dict["type"],
    )

    func(event)


@_util.copy_func_kwargs(_options.StorageOptions)
def on_object_archived(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler sent only when a bucket has enabled object versioning.
    This event indicates that the live version of an object has become an
    archived version, either because it was archived or because it was
    overwritten by the upload of an object of the same name.

    Example::
      @on_object_archived()
      def example(event: CloudEvent[StorageObjectData]) -> None:
          pass

    """
    options = _options.StorageOptions(**kwargs)

    def on_object_archived_inner_decorator(func: _C1):

        @_functools.wraps(func)
        def on_object_archived_wrapped(raw: _ce.CloudEvent):
            return _message_handler(func, raw)

        _util.set_func_endpoint_attr(
            on_object_archived_wrapped,
            options._endpoint(func_name=func.__name__,
                              event_type=_event_type_archived),
        )
        return on_object_archived_wrapped

    return on_object_archived_inner_decorator


@_util.copy_func_kwargs(_options.StorageOptions)
def on_object_finalized(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler which fires every time a Google Cloud Storage object
    creation occurs.
    Sent when a new object (or a new generation of an existing object)
    is successfully created in the bucket. This includes copying or rewriting
    an existing object. A failed upload does not trigger this event.

    Example::
      @on_object_finalized()
      def example(event: CloudEvent[StorageObjectData]) -> None:
          pass

    """
    options = _options.StorageOptions(**kwargs)

    def on_object_finalized_inner_decorator(func: _C1):

        @_functools.wraps(func)
        def on_object_finalized_wrapped(raw: _ce.CloudEvent):
            return _message_handler(func, raw)

        _util.set_func_endpoint_attr(
            on_object_finalized_wrapped,
            options._endpoint(func_name=func.__name__,
                              event_type=_event_type_finalized),
        )
        return on_object_finalized_wrapped

    return on_object_finalized_inner_decorator


@_util.copy_func_kwargs(_options.StorageOptions)
def on_object_deleted(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler which fires every time a Google Cloud Storage deletion occurs.
    Sent when an object has been permanently deleted. This includes objects
    that are overwritten or are deleted as part of the bucket's lifecycle
    configuration. For buckets with object versioning enabled, this is not
    sent when an object is archived, even if archival occurs
    via the `storage.objects.delete` method.

    Example::
      @on_object_deleted()
      def example(event: CloudEvent[StorageObjectData]) -> None:
          pass

    """
    options = _options.StorageOptions(**kwargs)

    def on_object_deleted_inner_decorator(func: _C1):

        @_functools.wraps(func)
        def on_object_deleted_wrapped(raw: _ce.CloudEvent):
            return _message_handler(func, raw)

        _util.set_func_endpoint_attr(
            on_object_deleted_wrapped,
            options._endpoint(func_name=func.__name__,
                              event_type=_event_type_deleted),
        )
        return on_object_deleted_wrapped

    return on_object_deleted_inner_decorator


@_util.copy_func_kwargs(_options.StorageOptions)
def on_object_metadata_updated(**kwargs) -> _typing.Callable[[_C1], _C1]:
    """
    Event handler which fires every time the metadata of an existing object
    changes.

    Example::
      @on_object_metadata_updated()
      def example(event: CloudEvent[StorageObjectData]) -> None:
          pass

    """
    options = _options.StorageOptions(**kwargs)

    def on_object_metadata_updated_inner_decorator(func: _C1):

        @_functools.wraps(func)
        def on_object_metadata_updated_wrapped(raw: _ce.CloudEvent):
            return _message_handler(func, raw)

        _util.set_func_endpoint_attr(
            on_object_metadata_updated_wrapped,
            options._endpoint(func_name=func.__name__,
                              event_type=_event_type_metadata_updated),
        )
        return on_object_metadata_updated_wrapped

    return on_object_metadata_updated_inner_decorator
