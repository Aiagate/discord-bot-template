"""Generic Result type, inspired by Rust's Result type."""

from collections.abc import Awaitable, Callable, Coroutine, Generator, Sequence
from dataclasses import dataclass
from typing import Any, Never, TypeGuard, TypeVar

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Success type for map/and_then


@dataclass(frozen=True)
class Ok[T]:
    """Represents a successful result."""

    value: T

    def map[V](self, f: Callable[[T], V]) -> "Ok[V]":
        """
        Transform the Ok value using the provided function.

        Args:
            f: Function to apply to the Ok value (T -> V)

        Returns:
            Ok[V] containing the transformed value

        Example:
            Ok(5).map(lambda x: x * 2)  # Returns Ok(10)
        """
        return Ok(f(self.value))

    def and_then[V, F](self, f: Callable[[T], "Result[V, F]"]) -> "Result[V, F]":
        """
        Apply a function that returns a Result, flattening the nested Result.

        This is the monadic bind operation (flatMap in some languages).
        Enables chaining operations that may fail.

        Args:
            f: Function that takes the Ok value and returns a new Result (T -> Result[V, F])

        Returns:
            Result[V, F] - The result of applying the function

        Example:
            Ok(5).and_then(lambda x: Ok(x * 2))  # Returns Ok(10)
            Ok(5).and_then(lambda x: Err("failed"))  # Returns Err("failed")
        """
        return f(self.value)

    def unwrap(self) -> T:
        """
        Return the Ok value.

        Returns:
            The wrapped value
        """
        return self.value


@dataclass(frozen=True)
class Err[E]:
    """Represents a failure result."""

    error: E

    def map[V](self, f: Callable[[Any], Any]) -> "Err[E]":
        """
        Pass through the error unchanged (Railway-oriented programming pattern).

        Args:
            f: Function that would be applied (ignored for Err)

        Returns:
            Self (unchanged Err)
        """
        return self

    def and_then[V, F](self, f: Callable[[Any], "Result[V, F]"]) -> "Err[E]":
        """
        Pass through the error unchanged (Railway-oriented programming pattern).

        Since this is an Err, the function is not called and the error propagates.

        Args:
            f: Function that would be applied (ignored for Err)

        Returns:
            Self (unchanged Err)

        Example:
            Err("error").and_then(lambda x: Ok(x * 2))  # Returns Err("error")
        """
        return self

    def unwrap(self) -> Never:
        """
        Raise the error as an exception.

        Raises:
            The error object (must be an Exception subclass)

        Raises:
            RuntimeError: If error is not an Exception
        """
        if isinstance(self.error, Exception):
            raise self.error
        else:
            raise RuntimeError(f"Error: {self.error}")


Result = Ok[T] | Err[E]


def is_ok[T, E](result: Result[T, E]) -> TypeGuard[Ok[T]]:
    """Return true if the result is ok."""
    return isinstance(result, Ok)


def is_err[T, E](result: Result[T, E]) -> TypeGuard[Err[E]]:
    """Return true if the result is an error."""
    return isinstance(result, Err)


def combine[E](results: Sequence[Result[Any, E]]) -> Result[list[Any], E]:
    """
    Aggregates a sequence of Result objects.

    If all results are Ok, returns an Ok containing a list of all success values.
    If any result is an Err, returns the first Err encountered.
    This version handles heterogeneous types in the input sequence.

    Args:
        results: A sequence of Result objects with potentially different success types.

    Returns:
        A single Result object. Ok(list of success values) or the first Err.
    """
    values: list[Any] = []
    for r in results:
        if is_err(r):
            return r  # Return the first error found
        values.append(r.unwrap())
    return Ok(values)


def combine_errors[T, E](results: Sequence[Result[T, E]]) -> Result[list[T], list[E]]:
    """
    Aggregates a sequence of Result objects, collecting all errors.

    If all results are Ok, returns an Ok containing a list of all success values.
    If any result is an Err, returns an Err containing a list of all error values.

    Args:
        results: A sequence of Result objects.

    Returns:
        A single Result. Ok(list of success values) or Err(list of all errors).
    """
    values: list[T] = []
    errors: list[E] = []
    for r in results:
        if is_err(r):
            errors.append(r.error)
        else:
            values.append(r.unwrap())

    if errors:
        return Err(errors)

    return Ok(values)


class ResultAwaitable[T, E]:
    """
    Awaitable wrapper for Result that enables method chaining before await.

    This allows elegant syntax like:
        message = await Mediator.send_async(query).map(...).unwrap()
    """

    def __init__(self, coro: Coroutine[Any, Any, Result[T, E]]) -> None:
        """
        Initialize with a coroutine that returns a Result.

        Args:
            coro: Coroutine that will return Result[T, E]
        """
        self._coro = coro

    def __await__(self) -> Generator[Any, None, Result[T, E]]:
        """Make this object awaitable, returning the underlying Result."""
        return self._coro.__await__()

    def map(self, f: Callable[[T], U]) -> "ResultAwaitable[U, E]":
        """
        Transform the Ok value using the provided function.

        This method chains onto the coroutine, creating a new coroutine that:
        1. Awaits the current Result
        2. Applies .map() to transform the value
        3. Returns the transformed Result

        Args:
            f: Function to apply to the Ok value (T -> U)

        Returns:
            ResultAwaitable[U, E] wrapping the transformed result

        Example:
            user_id = await Mediator.send_async(cmd).map(lambda v: v.user_id)
        """

        async def mapped() -> Result[U, E]:
            _result: Result[T, E] = await self
            return _result.map(f)

        return ResultAwaitable(mapped())

    def and_then(
        self, f: Callable[[T], Awaitable[Result[U, E]]]
    ) -> "ResultAwaitable[U, E]":
        """
        Apply an async function that returns a Result, flattening the nested Result.

        This enables chaining async operations that may fail.

        Args:
            f: Async function that takes the Ok value and returns a new Result
               (T -> Awaitable[Result[U, E]])

        Returns:
            ResultAwaitable[U, E] wrapping the result of applying the function

        Example:
            await (
                Mediator.send_async(create_cmd)
                .and_then(lambda result: Mediator.send_async(GetQuery(result.id)))
                .map(lambda value: format_message(value))
                .unwrap()
            )
        """

        async def chained() -> Result[U, E]:
            _result: Result[T, E] = await self
            match _result:
                case Ok(value):
                    return await f(value)
                case Err():
                    return _result

        return ResultAwaitable(chained())

    def unwrap(self) -> Awaitable[T]:
        """
        Return the Ok value or raise the Err as an exception.

        This is a terminal operation that unwraps the Result.

        Returns:
            Awaitable[T] that will return the value or raise the error

        Example:
            message = await Mediator.send_async(query).map(...).unwrap()
        """

        async def unwrapped() -> T:
            _result: Result[T, E] = await self
            return _result.unwrap()

        return unwrapped()
