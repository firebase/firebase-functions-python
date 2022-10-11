"""
Module for internal utilities.
"""

import typing as _typing

P = _typing.ParamSpec("P")
R = _typing.TypeVar("R")


class Sentinel:
    """Internal class for USE_DEFAULT."""

    def __init__(self, description):
        self.description = description


def copy_func_kwargs(
    func_with_kwargs: _typing.Callable[P, _typing.Any],  # pylint: disable=unused-argument
) -> _typing.Callable[[_typing.Callable[..., R]], _typing.Callable[P, R]]:

    def return_func(func: _typing.Callable[..., R]) -> _typing.Callable[P, R]:
        return _typing.cast(_typing.Callable[P, R], func)

    return return_func


def set_func_endpoint_attr(
        func: _typing.Callable[P, _typing.Any],
        endpoint: _typing.Any) -> _typing.Callable[P, _typing.Any]:
    setattr(func, "__firebase_endpoint__", endpoint)
    return func


def prune_nones(obj: dict) -> dict:
    for key in obj:
        if obj[key] is None:
            del obj[key]
        elif isinstance(obj[key], dict):
            prune_nones(obj[key])
    return obj
