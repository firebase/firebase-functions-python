"""
Logger module for Firebase Functions.
"""

import enum as _enum
import json as _json
import sys as _sys
import typing as _typing
import typing_extensions as _typing_extensions


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


def _entry_from_args(severity: LogSeverity, *args, **kwargs) -> LogEntry:
    """
    Creates a `LogEntry` from the given arguments.
    """

    message: str = " ".join([
        value
        if isinstance(value, str) else _json.dumps(_remove_circular(value))
        for value in args
    ])

    other: _typing.Dict[str, _typing.Any] = {
        key: value if isinstance(value, str) else _remove_circular(value)
        for key, value in kwargs.items()
    }

    entry: _typing.Dict[str, _typing.Any] = {"severity": severity, **other}
    if message:
        entry["message"] = message

    return _typing.cast(LogEntry, entry)


def _remove_circular(obj: _typing.Any,
                     refs: _typing.Set[_typing.Any] | None = None):
    """
    Removes circular references from the given object and replaces them with "[CIRCULAR]".
    """

    if refs is None:
        refs = set()

    if id(obj) in refs:
        return "[CIRCULAR]"

    if not isinstance(obj, (str, int, float, bool, type(None))):
        refs.add(id(obj))

    if isinstance(obj, dict):
        return {key: _remove_circular(value, refs) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_remove_circular(value, refs) for _, value in enumerate(obj)]
    elif isinstance(obj, tuple):
        return tuple(
            _remove_circular(value, refs) for _, value in enumerate(obj))
    else:
        return obj


def _get_write_file(severity: LogSeverity) -> _typing.TextIO:
    if severity == LogSeverity.ERROR:
        return _sys.stderr
    return _sys.stdout


def write(entry: LogEntry) -> None:
    write_file = _get_write_file(entry["severity"])
    print(_json.dumps(_remove_circular(entry)), file=write_file)


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
