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
            else _json.dumps(_coerce_json_safe(_remove_circular(value)), ensure_ascii=False)
            for value in args
        ]
    )

    other: dict[str, _typing.Any] = {
        key: value if isinstance(value, str) else _coerce_json_safe(_remove_circular(value))
        for key, value in kwargs.items()
    }

    entry: dict[str, _typing.Any] = {"severity": severity, **other}
    if message:
        entry["message"] = message
    if severity == LogSeverity.ERROR:
        stack_trace = _stack_trace_from_args(args, kwargs)
        if stack_trace is not None:
            entry["stack_trace"] = stack_trace

    return _typing.cast(LogEntry, entry)


def _stack_trace_from_exception(exception: BaseException) -> str | None:
    """
    Returns a formatted stack trace for an exception when available.
    """

    if exception.__traceback__ is not None:
        try:
            return "".join(
                _traceback.format_exception(exception.__class__, exception, exception.__traceback__)
            )
        except Exception:
            stack_trace = "".join(_traceback.format_tb(exception.__traceback__))
            stack_trace += f"{exception.__class__.__name__}: {_safe_exception_string(exception)}\n"
            return stack_trace
    return None


def _stack_trace_from_exception_type(exception_type: type[BaseException]) -> str | None:
    """
    Returns the active stack trace when the given type matches the current exception.
    """

    exc_type, exc_value, exc_traceback = _sys.exc_info()
    if exc_type is exception_type and exc_value is not None:
        if exc_traceback is not None:
            return "".join(_traceback.format_exception(exc_type, exc_value, exc_traceback))
    return None


def _stack_trace_from_args(
    args: tuple[_typing.Any, ...], kwargs: dict[str, _typing.Any]
) -> str | None:
    """
    Returns the first available stack trace from logger arguments or active exception state.
    """

    for value in (*args, *kwargs.values()):
        if isinstance(value, BaseException):
            stack_trace = _stack_trace_from_exception(value)
            if stack_trace is not None:
                return stack_trace
        elif isinstance(value, type) and issubclass(value, BaseException):
            stack_trace = _stack_trace_from_exception_type(value)
            if stack_trace is not None:
                return stack_trace

    exc_type, exc_value, exc_traceback = _sys.exc_info()
    if exc_type is not None and exc_value is not None and exc_traceback is not None:
        return "".join(_traceback.format_exception(exc_type, exc_value, exc_traceback))

    return None


def _safe_exception_string(exception: BaseException) -> str:
    """
    Returns a string representation of an exception without propagating repr/str errors.
    """

    try:
        return str(exception)
    except Exception:
        return exception.__class__.__name__


def _coerce_json_safe(obj: _typing.Any):
    """
    Converts values that survive circular-reference removal into JSON-safe values.
    """

    if isinstance(obj, str | int | float | bool | type(None)):
        return obj
    if isinstance(obj, dict):
        return {
            _coerce_json_safe_dict_key(key): _coerce_json_safe(value) for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [_coerce_json_safe(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(_coerce_json_safe(item) for item in obj)
    return _safe_repr(obj)


def _coerce_json_safe_dict_key(obj: _typing.Any):
    """
    Converts dictionary keys into values accepted by JSON object encoding.
    """

    if isinstance(obj, str | int | float | bool | type(None)):
        return obj
    coerced = _coerce_json_safe(obj)
    if isinstance(coerced, str | int | float | bool | type(None)):
        return coerced
    return _safe_repr(coerced)


def _safe_repr(obj: _typing.Any) -> str:
    """
    Returns a repr without propagating repr errors.
    """

    try:
        return repr(obj)
    except Exception:
        return obj.__class__.__name__


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
    if isinstance(obj, dict):
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
