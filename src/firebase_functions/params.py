"""Module for params that can make Cloud Functions codebases generic."""

from abc import ABC
from dataclasses import dataclass
import os
from typing import Generic, TypeVar, Optional, Union

T = TypeVar("T", str, int, float, bool, list)


@dataclass(frozen=True)
class Expression(ABC, Generic[T]):
    """
    A CEL expression which can be evaluated during function deployment, and
    resolved to a value of the generic type parameter: i.e, you can pass
    an Expression<number> as the value of an option that normally accepts numbers.
    """

    def value(self) -> T:
        """
        Returns the Expression's runtime value, based on the CLI's resolution of params.
        """
        raise NotImplementedError()

    def to_cel(self) -> str:
        """
        Returns the Expression's representation as a braced CEL expression.
        """
        return f"{{ {self} }}"


def _quote_if_string(literal: T) -> T:
    return literal if not isinstance(literal, str) else f'"{literal}"'


@dataclass(frozen=True)
class TernaryExpression(Expression[T], Generic[T]):
    test: Expression[bool]
    if_true: T
    if_false: T

    def value(self) -> T:
        return self.if_true if self.test.value() else self.if_false

    def __str__(self) -> str:
        return f"{self.test} ? {_quote_if_string(self.if_true)} : {_quote_if_string(self.if_false)}"


@dataclass(frozen=True)
class CompareExpression(Expression[bool], Generic[T]):
    """
    A CEL expression that evaluates to boolean true or false based on a comparison
    between the value of another expression and a literal of that same type.
    """
    comparator: str
    left: Expression[T]
    right: T

    def value(self) -> bool:
        left: T = self.left.value()
        if self.comparator == "==":
            return left == self.right
        elif self.comparator == ">":
            return left > self.right
        elif self.comparator == ">=":
            return left >= self.right
        elif self.comparator == "<":
            return left < self.right
        elif self.comparator == "<=":
            return left <= self.right
        else:
            raise ValueError(f"Unknown comparator {self.comparator}")

    def __str__(self) -> str:
        return f"{self.left} {self.comparator} {_quote_if_string(self.right)}"

    def then(self, if_true: T, if_false: T) -> TernaryExpression[T]:
        return TernaryExpression(self, if_true, if_false)


@dataclass(frozen=True)
class SelectOptions(Generic[T]):
    """
    A representation of an option that can be selected via a SelectInput.
    """

    value: T
    """The value of the option."""

    label: Optional[str] = None
    """The displayed label for the option."""


@dataclass(frozen=True)
class SelectInput(Generic[T]):
    """
    Specifies that a Param's value should be determined by having the user select
    from a list of pre-canned options interactively at deploy-time.
    """

    options: list[SelectOptions[T]]
    """A list of user selectable options."""


@dataclass(frozen=True)
class TextInput:
    """
    Specifies that a Param's value should be determined by prompting the user
    to type it in interactively at deploy-time. Input that does not match the provided
    validation_regex, if present, will be retried.
    """

    example: Optional[str] = None
    """
    An example of the input required that will be displayed alongside the input prompt.
    """

    validation_regex: Optional[str] = None
    """
    Validation regex for the input.
    Input that does not match this regex, if present, will be retried.
    """

    validation_error_message: Optional[str] = None
    """
    An error message that is displayed to the user if validation_regex fails.
    """


@dataclass(frozen=True)
class ResourceInput:
    """
    Specifies that a Param's value should be determined by having the user
    select from a list containing all the project's resources of a certain
    type. Currently, only type:"storage.googleapis.com/Bucket" is supported.
    """

    type: str
    """
    The resource type. Currently, only type:"storage.googleapis.com/Bucket" is supported.
    """


@dataclass(frozen=True)
class Param(Expression[T]):
    """
    A param is a declared dependency on an external value.
    """

    name: str
    """
    The environment variable of this parameter. Must be upper case.
    """

    default: Optional[T] = None
    """
    The default value to assign to this param if none provided.
    """

    label: Optional[str] = None
    """
    A label that is displayed to the user for this param.
    """

    description: Optional[str] = None
    """
    Description of this param that is displayed to the user.
    """

    immutable: Optional[bool] = None
    """
    Whether the value of this parameter can change between function
    deployments.
    """

    input: Union[TextInput, ResourceInput, SelectInput[T]] = TextInput()
    """
    The type of input that is required for this param, e.g. TextInput.
    """

    def value(self) -> T:
        raise NotImplementedError()

    def compare(self, compare: str, right: T) -> CompareExpression:
        return CompareExpression(compare, self, right)

    def equals(self, right: T) -> CompareExpression:
        return self.compare("==", right)

    def __str__(self) -> str:
        return f"params.{self.name}"


@dataclass(frozen=True)
class SecretParam(Expression[str]):
    """
    A secret param is a declared dependency on an external secret.
    """

    name: str
    """
    The environment variable of this parameter. Must be upper case.
    """

    label: Optional[str] = None
    """
    A label that is displayed to the user for this param.
    """

    description: Optional[str] = None
    """
    Description of this param that is displayed to the user.
    """

    immutable: Optional[bool] = None
    """
    Whether the value of this parameter can change between function
    deployments.
    """

    def __str__(self):
        return f"{{{{ params.{self.name} }}}}"

    def value(self) -> str:
        """Current value of this parameter."""
        return os.environ.get(self.name, "")

    def compare(self, compare: str, right: T) -> CompareExpression:
        return CompareExpression(compare, self, right)

    def equals(self, right: T) -> CompareExpression:
        return self.compare("==", right)


@dataclass(frozen=True)
class StringParam(Param):
    """A parameter as a string value."""

    def value(self) -> str:
        if os.environ.get(self.name) is not None:
            return os.environ[self.name]

        if self.default is not None:
            return self.default

        return str()


@dataclass(frozen=True)
class IntParam(Param[int]):
    """A parameter as a int value."""

    def value(self) -> int:
        if os.environ.get(self.name) is not None:
            return int(os.environ[self.name])
        if self.default is not None:
            return self.default
        return int()


@dataclass(frozen=True)
class FloatParam(Param[float]):
    """A parameter as a float value."""

    def value(self) -> float:
        if os.environ.get(self.name) is not None:
            return float(os.environ[self.name])
        if self.default is not None:
            return self.default
        return float()


@dataclass(frozen=True)
class BoolParam(Param[bool]):
    """A parameter as a bool value."""

    def value(self) -> bool:
        env_value = os.environ.get(self.name)
        if env_value is not None:
            if env_value.lower() in ["true", "t", "1", "y", "yes"]:
                return True
            if env_value.lower() in ["false", "f", "0", "n", "no"]:
                return False
            raise ValueError(f"Invalid value for {self.name}: {env_value}")
        if self.default is not None:
            return self.default
        return False


@dataclass(frozen=True)
class ListParam(Param[list]):
    """A parameter as a list of strings."""

    def value(self) -> list[str]:
        if os.environ.get(self.name) is not None:
            return list(filter(len, os.environ[self.name].split(",")))
        if self.default is not None:
            return self.default
        return []


PROJECT_ID = StringParam("GCLOUD_PROJECT",
                         description="The active Firebase project")

STORAGE_BUCKET = StringParam(
    "STORAGE_BUCKET",
    description="The default Cloud Storage for Firebase bucket")

DATABASE_URL = StringParam(
    "DATABASE_URL",
    description="The Firebase project's default Realtime Database instance URL",
)

DATABASE_INSTANCE = StringParam(
    "DATABASE_INSTANCE",
    description="The Firebase project's default Realtime Database instance name",
)

EXTENSION_ID = StringParam(
    "EXT_INSTANCE_ID",
    label="Extension instance ID",
    description="When a function is running as part of an extension, "
    "this is the unique identifier for the installed extension "
    "instance",
    default="",
)
