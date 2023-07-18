import enum as _enum
import json as _json
import typing as _typing
import typing_extensions as _typing_extensions
import logging as _logging
import sys as _sys

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 
stream_handler = _logging.StreamHandler(_sys.stdout)

_logging.basicConfig(format=log_format, level=_logging.DEBUG, handlers=[stream_handler])


logger = _logging.getLogger()
logger.setLevel(_logging.DEBUG)


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

# class LogEntry(_google_cloud_logging.LogEntry):
#     # is this the correct way to reexport/extend the class?
#     def __init__(self, **kwargs):
#         super().__init__(self,**kwargs)
#     pass

# a function that removes circular references and replaces them with [Circular]
def _replace_circular(obj, seen=None):
    if seen is None:
        seen = set()

    if (id(obj) in seen):
        return "[CIRCULAR]"
    if not isinstance(obj, (str, int, float, bool, type(None))):
        seen.add(id(obj))

    if isinstance(obj, dict):
        return {
            key: _replace_circular(value, seen) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [_replace_circular(value, seen) for i, value in enumerate(obj)]
    elif isinstance(obj, tuple):
        return tuple(_replace_circular(value, seen) for i, value in enumerate(obj))
    else:
        return obj


def _entry_from_args(severity: LogSeverity, **kwargs) -> LogEntry:
    """
    Creates a `LogEntry` from the given arguments.
    """

    message: str = " ".join(
        # do we need to replace_circular here?
        [value if isinstance(value,str) else _json.dumps(_replace_circular(value)) for value in kwargs.values() ]
    )

    return {
        "severity": severity,
        "message": message
    }

def write(entry: LogEntry) -> None:
    """
    Writes a `LogEntry` to `stdout`/`stderr` (depending on severity).
    """
    severity = entry['severity']

    out = _json.dumps(_replace_circular(entry))

    match severity:
        case LogSeverity.DEBUG:
            logger.debug(out)
        case LogSeverity.INFO:
            logger.info(out)
        case LogSeverity.NOTICE:
            logger.info(out)
        case LogSeverity.WARNING:
            logger.warning(out)
        case LogSeverity.ERROR:
            logger.error(out)
        case LogSeverity.CRITICAL:
            logger.critical(out)
        case LogSeverity.ALERT:
            logger.critical(out)
        case LogSeverity.EMERGENCY:
            _logging.critical(out)

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