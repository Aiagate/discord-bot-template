"""Generic Result type, inspired by Rust's Result type."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeVar

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type


@dataclass(frozen=True)
class Ok[T]:
    """Represents a successful result."""

    value: T

    @property
    def is_ok(self) -> Literal[True]:
        return True

    @property
    def is_err(self) -> Literal[False]:
        return False


@dataclass(frozen=True)
class Err[E]:
    """Represents a failure result."""

    error: E

    @property
    def is_ok(self) -> Literal[False]:
        return False

    @property
    def is_err(self) -> Literal[True]:
        return True


Result = Ok[T] | Err[E]


def combine[T, E](results: Sequence[Result[T, E]]) -> Result[tuple[T, ...], E]:
    """
    Aggregates a sequence of Result objects.

    If all results are Ok, returns an Ok containing a tuple of all success values.
    If any result is an Err, returns the first Err encountered.

    Args:
        results: A sequence of Result objects.

    Returns:
        A single Result object.
    """
    values: list[T] = []
    for r in results:
        match r:
            case Ok(value):
                values.append(value)
            case Err():
                # Return the first error found
                return r
    # If the loop completes without returning, all were Ok.
    return Ok(tuple(values))
