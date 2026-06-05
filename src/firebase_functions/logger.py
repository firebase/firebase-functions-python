"""
Logger module for Firebase Functions.
"""

import enum as _enum
import json as _json
import sys as _sys
import traceback as _traceback
import typing as _typing

import typing_extensions as _typing_extensions

# If encoding is not 'utf-8', change it to 'utf-8'.
if _sys.stdout.encoding != "utf-8":
    _sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
if _sys.stderr.encoding != "utf-8":
    _sys.stderr.reconfigure(encoding="utf-8")  # type: ignore


class LogSeverity(str, _enum.Enum):
    """
    `LogSeverity` indicates the detailed severity of the log entry. See
    `LogSeverity <https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#logseverity>`.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"

    def __str__(self) -> str:
        return self.value


class LogEntry(_typing.TypedDict):
    """
    `LogEntry` represents a log entry.
    See `LogEntry <https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry>`_.
    """

    severity: _typing_extensions.Required[LogSeverity]
    message: _typing_extensions.NotRequired[str]
    stack_trace: _typing_extensions.NotRequired[str]


def _entry_from_args(severity: LogSeverity, *args, **kwargs) -> LogEntry:
    """
    Creates a `LogEntry` from the given arguments.
    """

    message: str = " ".join(
        [
            value
            if isinstance(value, str)
            else _json.dumps(_remove_circular(value), ensure_ascii=False)
            for value in args
        ]
    )

    other: dict[str, _typing.Any] = {
        key: value if isinstance(value, str) else _remove_circular(value)
        for key, value in kwargs.items()
    }

    entry: dict[str, _typing.Any] = {"severity": severity, **other}
    if message:
        entry["message"] = message

    return _typing.cast(LogEntry, entry)


def _exception_from_args(
    exception: BaseException, refs: set[int] | None = None
) -> dict[str, _typing.Any]:
    """
    Creates a JSON-safe representation of an exception.
    """

    details: dict[str, _typing.Any] = {
        "type": exception.__class__.__name__,
        "message": _safe_exception_string(exception),
    }
    if exception.args:
        details["args"] = _json_safe_exception_args(exception.args, refs)
    if exception.__traceback__ is not None:
        try:
            details["stack_trace"] = "".join(
                _traceback.format_exception(exception.__class__, exception, exception.__traceback__)
            )
        except Exception:
            details["stack_trace"] = "".join(_traceback.format_tb(exception.__traceback__))
            details["stack_trace"] += f"{exception.__class__.__name__}: {details['message']}\n"
    return details


def _exception_type_from_args(
    exception_type: type[BaseException],
) -> dict[str, _typing.Any]:
    """
    Creates a JSON-safe representation of an exception class.

    If the class matches the active exception from `sys.exc_info()`, include
    the current exception message and stack trace as well.
    """

    details: dict[str, _typing.Any] = {
        "type": exception_type.__name__,
        "message": exception_type.__name__,
    }
    exc_type, exc_value, exc_traceback = _sys.exc_info()
    if exc_type is exception_type and exc_value is not None:
        details["message"] = _safe_exception_string(exc_value)
        if exc_traceback is not None:
            details["stack_trace"] = "".join(
                _traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
    return details


def _safe_exception_string(exception: BaseException) -> str:
    """
    Returns a string representation of an exception without propagating repr/str errors.
    """

    try:
        return str(exception)
    except Exception:
        return exception.__class__.__name__


def _json_safe_exception_args(args: tuple[_typing.Any, ...], refs: set[int] | None = None):
    """
    Returns exception args in a form that can be encoded as JSON.
    """

    return _coerce_json_safe(_remove_circular(args, refs))


def _coerce_json_safe(obj: _typing.Any):
    """
    Converts values that survive circular-reference removal into JSON-safe values.
    """

    if isinstance(obj, str | int | float | bool | type(None)):
        return obj
    if isinstance(obj, dict):
        return {key: _coerce_json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_coerce_json_safe(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(_coerce_json_safe(item) for item in obj)
    return repr(obj)


def _remove_circular(obj: _typing.Any, refs: set[int] | None = None):
    """
    Removes circular references from the given object and replaces them with "[CIRCULAR]".
    """

    if refs is None:
        refs = set()

    # Check if the object is already in the current recursion stack
    if id(obj) in refs:
        return "[CIRCULAR]"

    # For non-primitive objects, add the current object's id to the recursion stack
    if not isinstance(obj, str | int | float | bool | type(None)):
        refs.add(id(obj))

    # Recursively process the object based on its type
    result: _typing.Any
    if isinstance(obj, BaseException):
        result = _exception_from_args(obj, refs)
    elif isinstance(obj, type) and issubclass(obj, BaseException):
        result = _exception_type_from_args(obj)
    elif isinstance(obj, dict):
        result = {key: _remove_circular(value, refs) for key, value in obj.items()}
    elif isinstance(obj, list):
        result = [_remove_circular(item, refs) for item in obj]
    elif isinstance(obj, tuple):
        result = tuple(_remove_circular(item, refs) for item in obj)
    else:
        result = obj

    # Remove the object's id from the recursion stack after processing
    if not isinstance(obj, str | int | float | bool | type(None)):
        refs.remove(id(obj))

    return result


def _get_write_file(severity: LogSeverity) -> _typing.TextIO:
    if severity == LogSeverity.ERROR:
        return _sys.stderr
    return _sys.stdout


def write(entry: LogEntry) -> None:
    write_file = _get_write_file(entry["severity"])
    print(_json.dumps(_remove_circular(entry), ensure_ascii=False), file=write_file)


def debug(*args, **kwargs) -> None:
    """
    Logs a debug message.
    """
    write(_entry_from_args(LogSeverity.DEBUG, *args, **kwargs))


def log(*args, **kwargs) -> None:
    """
    Logs a log message.
    """
    write(_entry_from_args(LogSeverity.NOTICE, *args, **kwargs))


def info(*args, **kwargs) -> None:
    """
    Logs an info message.
    """
    write(_entry_from_args(LogSeverity.INFO, *args, **kwargs))


def warn(*args, **kwargs) -> None:
    """
    Logs a warning message.
    """
    write(_entry_from_args(LogSeverity.WARNING, *args, **kwargs))


def error(*args, **kwargs) -> None:
    """
    Logs an error message.
    """
    write(_entry_from_args(LogSeverity.ERROR, *args, **kwargs))


def exception(*args, **kwargs) -> None:
    """
    Logs an error message and includes the active stack trace.
    """
    entry = _entry_from_args(LogSeverity.ERROR, *args, **kwargs)
    exc_type, exc_value, exc_traceback = _sys.exc_info()
    if exc_type is not None and exc_value is not None and exc_traceback is not None:
        entry["stack_trace"] = "".join(
            _traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
    write(entry)
