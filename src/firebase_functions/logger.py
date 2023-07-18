import enum as _enum
import json as _json
import sys as _sys
import typing as _typing
import typing_extensions as _typing_extensions


class LogSeverity(str, _enum.Enum):
    """
    `LogSeverity` indicates the detailed severity of the log entry. See [LogSeverity](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#logseverity).
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"


class LogEntry(_typing.TypedDict):
    """
    `LogEntry` represents a log entry.
    See [LogEntry](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry).
    """

    severity: _typing_extensions.Required[LogSeverity]
    message: _typing_extensions.NotRequired[str]


def _entry_from_args(severity: LogSeverity, **kwargs) -> LogEntry:
    """
    Creates a `LogEntry` from the given arguments.
    """

    message: str = " ".join(
        # do we need to replace_circular here?
        [
            value if isinstance(value, str) else _json.dumps(
                _remove_circular(value)) for value in kwargs.values()
        ])

    return {"severity": severity, "message": message}


def _remove_circular(obj: _typing.Any, refs: _typing.Set[_typing.Any] = set()):
    """
    Removes circular references from the given object and replaces them with "[CIRCULAR]".
    """

    if (id(obj) in refs):
        return "[CIRCULAR]"

    if not isinstance(obj, (str, int, float, bool, type(None))):
        refs.add(id(obj))

    if isinstance(obj, dict):
        return {key: _remove_circular(value, refs) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_remove_circular(value, refs) for _, value in enumerate(obj)]
    elif isinstance(obj, tuple):
        return tuple(_remove_circular(value, refs) for _, value in enumerate(obj))
    else:
        return obj


def _get_write_file(severity: LogSeverity) -> _typing.TextIO:
    if severity == LogSeverity.ERROR:
        return _sys.stderr
    return _sys.stdout


def write(entry: LogEntry) -> None:
    write_file = _get_write_file(entry['severity'])
    print(_json.dumps(_remove_circular(entry)), file=write_file)


def debug(**kwargs) -> None:
    """
    Logs a debug message.
    """
    write(_entry_from_args(LogSeverity.DEBUG, **kwargs))


def log(**kwargs) -> None:
    """
    Logs a log message.
    """
    write(_entry_from_args(LogSeverity.NOTICE, **kwargs))


def info(**kwargs) -> None:
    """
    Logs an info message.
    """
    write(_entry_from_args(LogSeverity.INFO, **kwargs))


def warn(**kwargs) -> None:
    """
    Logs a warning message.
    """
    write(_entry_from_args(LogSeverity.WARNING, **kwargs))


def error(**kwargs) -> None:
    """
    Logs an error message.
    """
    write(_entry_from_args(LogSeverity.ERROR, **kwargs))
