"""Tests for Result type functional methods."""

import pytest

from app.core.result import Err, Ok
from app.usecases.result import ErrorType, UseCaseError


def test_ok_map_transforms_value() -> None:
    """Test that Ok.map transforms the value."""
    result: Ok[int] = Ok(5)
    mapped = result.map(lambda x: x * 2)

    assert isinstance(mapped, Ok)
    assert mapped.value == 10


def test_ok_map_changes_type() -> None:
    """Test that Ok.map can change the type of the value."""
    result: Ok[int] = Ok(42)
    mapped = result.map(lambda x: f"Number: {x}")

    assert isinstance(mapped, Ok)
    assert mapped.value == "Number: 42"


def test_err_map_passes_through() -> None:
    """Test that Err.map passes through unchanged."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="User not found")
    result: Err[UseCaseError] = Err(error)
    mapped = result.map(lambda x: x * 2)

    assert isinstance(mapped, Err)
    assert mapped.error is error
    assert mapped.error.message == "User not found"


def test_ok_unwrap_returns_value() -> None:
    """Test that Ok.unwrap returns the value."""
    result: Ok[int] = Ok(42)
    value = result.unwrap()

    assert value == 42


def test_err_expect_raises_exception() -> None:
    """Test that Err.expect raises with the provided message."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="User not found")
    result: Err[UseCaseError] = Err(error)

    with pytest.raises(RuntimeError) as exc_info:
        result.expect("Expected user to exist")

    assert "Expected user to exist" in str(exc_info.value)
    assert exc_info.value.__cause__ is error


def test_map_chain() -> None:
    """Test that multiple map calls can be chained."""
    result: Ok[int] = Ok(5)
    final = (
        result.map(lambda x: x * 2).map(lambda x: x + 3).map(lambda x: f"Result: {x}")
    )

    assert isinstance(final, Ok)
    assert final.value == "Result: 13"


def test_map_chain_with_err() -> None:
    """Test that map chain with Err passes through unchanged."""
    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Invalid input")
    result: Err[UseCaseError] = Err(error)
    final = (
        result.map(lambda x: x * 2).map(lambda x: x + 3).map(lambda x: f"Result: {x}")
    )

    assert isinstance(final, Err)
    assert final.error is error


def test_map_unwrap_chain() -> None:
    """Test that map and unwrap can be chained together."""
    result: Ok[int] = Ok(10)
    value = result.map(lambda x: x * 5).map(lambda x: x + 10).unwrap()

    assert value == 60


def test_map_expect_chain_with_err() -> None:
    """Test that map and expect chain raises on Err."""
    error = UseCaseError(type=ErrorType.UNEXPECTED, message="Something went wrong")
    result: Err[UseCaseError] = Err(error)

    with pytest.raises(RuntimeError) as exc_info:
        result.map(lambda x: x * 2).expect("Should not be an error")

    assert "Should not be an error" in str(exc_info.value)


def test_err_expect_with_non_exception() -> None:
    """Test that Err.expect raises RuntimeError for non-Exception errors."""
    result: Err[str] = Err("Not an exception")

    with pytest.raises(RuntimeError) as exc_info:
        result.expect("Expected success")

    assert "Expected success: Not an exception" in str(exc_info.value)


def test_usecase_error_str() -> None:
    """Test that UseCaseError.__str__ returns the message."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Resource not found")

    assert str(error) == "Resource not found"


def test_combine_all_ok() -> None:
    """Test that combine returns Ok with tuple of values when all are Ok."""
    from app.core.result import combine

    results = (Ok(1), Ok(2), Ok(3))
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == (1, 2, 3)


def test_combine_with_err() -> None:
    """Test that combine returns first Err when any result is Err."""
    from app.core.result import combine

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="First error")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Second error")
    results = (Ok(1), Err(error1), Ok(3), Err(error2))
    combined = combine(results)

    assert isinstance(combined, Err)
    assert combined.error is error1


def test_combine_empty_sequence() -> None:
    """Test that combine returns Ok with empty tuple for empty sequence."""
    from app.core.result import Result, combine

    results: tuple[Result[int, UseCaseError], ...] = ()
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == ()


def test_combine_single_ok() -> None:
    """Test that combine returns Ok with single-element tuple for one Ok."""
    from app.core.result import combine

    results = (Ok(42),)
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == (42,)


def test_combine_single_err() -> None:
    """Test that combine returns the Err when given a single Err."""
    from app.core.result import combine

    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")
    results = (Err(error),)
    combined = combine(results)

    assert isinstance(combined, Err)
    assert combined.error is error


def test_combine_multiple_errors_returns_first() -> None:
    """Test that combine returns first Err when multiple errors exist."""
    from app.core.result import combine

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="First")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Second")
    error3 = UseCaseError(type=ErrorType.UNEXPECTED, message="Third")
    results = (Err(error1), Err(error2), Err(error3))
    combined = combine(results)

    assert isinstance(combined, Err)
    assert combined.error is error1
    assert combined.error.message == "First"


def test_combine_preserves_string_type() -> None:
    """Test that combine preserves type of Ok values (string example)."""
    from app.core.result import combine

    results = (Ok("hello"), Ok("world"), Ok("test"))
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == ("hello", "world", "test")


def test_combine_error_after_ok_values() -> None:
    """Test that combine returns first Err even after Ok values."""
    from app.core.result import combine

    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Failed")
    results = (Ok(1), Ok(2), Err(error), Ok(4))
    combined = combine(results)

    assert isinstance(combined, Err)
    assert combined.error is error


def test_is_ok_returns_true_for_ok() -> None:
    """Test that is_ok returns True for Ok result."""
    from app.core.result import is_ok

    result = Ok(42)
    assert is_ok(result) is True


def test_is_ok_returns_false_for_err() -> None:
    """Test that is_ok returns False for Err result."""
    from app.core.result import Result, is_ok

    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")
    result: Result[int, UseCaseError] = Err(error)
    assert is_ok(result) is False


def test_combine_heterogeneous_two_types() -> None:
    """Test that combine handles two different types correctly."""
    from app.core.result import Result, combine

    user_id: Result[int, UseCaseError] = Ok(123)
    email: Result[str, UseCaseError] = Ok("user@example.com")

    combined = combine((user_id, email))

    assert isinstance(combined, Ok)
    assert combined.value == (123, "user@example.com")
    user_id_val, email_val = combined.value
    assert isinstance(user_id_val, int)
    assert isinstance(email_val, str)


def test_combine_heterogeneous_three_types() -> None:
    """Test that combine handles three different types correctly."""
    from app.core.result import Result, combine

    name: Result[str, UseCaseError] = Ok("Alice")
    age: Result[int, UseCaseError] = Ok(30)
    active: Result[bool, UseCaseError] = Ok(True)

    combined = combine((name, age, active))

    assert isinstance(combined, Ok)
    assert combined.value == ("Alice", 30, True)
    name_val, age_val, active_val = combined.value
    assert name_val == "Alice"
    assert age_val == 30
    assert active_val is True


def test_combine_heterogeneous_with_error() -> None:
    """Test that combine returns first error with heterogeneous types."""
    from app.core.result import Result, combine

    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Invalid age")
    name: Result[str, UseCaseError] = Ok("Bob")
    age: Result[int, UseCaseError] = Err(error)
    active: Result[bool, UseCaseError] = Ok(False)

    combined = combine((name, age, active))

    assert isinstance(combined, Err)
    assert combined.error is error


def test_combine_homogeneous_list_still_works() -> None:
    """Test that combine still works for homogeneous lists (backward compat)."""
    from app.core.result import combine

    results = (Ok(1), Ok(2), Ok(3), Ok(4))
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == (1, 2, 3, 4)


def test_combine_complex_heterogeneous_types() -> None:
    """Test combine with complex heterogeneous types."""
    from app.core.result import Result, combine

    user_id: Result[int, UseCaseError] = Ok(456)
    email: Result[str, UseCaseError] = Ok("test@example.com")
    age: Result[int, UseCaseError] = Ok(25)
    is_active: Result[bool, UseCaseError] = Ok(True)

    combined = combine((user_id, email, age, is_active))

    assert isinstance(combined, Ok)
    uid, mail, user_age, active = combined.value
    assert uid == 456
    assert mail == "test@example.com"
    assert user_age == 25
    assert active is True


def test_ok_and_then_returns_new_result() -> None:
    """Test that Ok.and_then applies the function and returns the new Result."""
    result: Ok[int] = Ok(5)
    new_result = result.and_then(lambda x: Ok(x * 2))

    assert isinstance(new_result, Ok)
    assert new_result.value == 10


def test_ok_and_then_propagates_error() -> None:
    """Test that Ok.and_then propagates error if function returns Err."""
    result: Ok[int] = Ok(5)
    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Failed")
    new_result = result.and_then(lambda x: Err(error))

    assert isinstance(new_result, Err)
    assert new_result.error is error


def test_err_and_then_passes_through() -> None:
    """Test that Err.and_then passes through unchanged."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")
    result: Err[UseCaseError] = Err(error)
    new_result = result.and_then(lambda x: Ok(x * 2))

    assert isinstance(new_result, Err)
    assert new_result.error is error


def test_and_then_chain() -> None:
    """Test that multiple and_then calls can be chained."""
    result: Ok[int] = Ok(2)
    final = (
        result.and_then(lambda x: Ok(x * 3))
        .and_then(lambda x: Ok(x + 10))
        .and_then(lambda x: Ok(f"Result: {x}"))
    )

    assert isinstance(final, Ok)
    assert final.value == "Result: 16"


def test_and_then_chain_with_error() -> None:
    """Test that error in and_then chain stops further processing."""
    result: Ok[int] = Ok(2)
    error = UseCaseError(type=ErrorType.UNEXPECTED, message="Error occurred")
    final = (
        result.and_then(lambda x: Ok(x * 3))
        .and_then(lambda x: Err(error))
        .and_then(lambda x: Ok(x + 10))  # type: ignore[arg-type]
    )

    assert isinstance(final, Err)
    assert final.error is error


def test_and_then_with_map() -> None:
    """Test that and_then and map can be combined."""
    result: Ok[int] = Ok(5)
    final = (
        result.and_then(lambda x: Ok(x * 2))
        .map(lambda x: x + 5)
        .and_then(lambda x: Ok(f"Final: {x}"))
    )

    assert isinstance(final, Ok)
    assert final.value == "Final: 15"


def test_ok_expect_returns_value() -> None:
    """Test that Ok.expect returns the value."""
    result: Ok[int] = Ok(42)
    value = result.expect("Should have value")

    assert value == 42


def test_aggregate_err_str() -> None:
    """Test AggregateErr string representation."""
    from app.core.result import AggregateErr

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="First error")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Second error")
    aggregate = AggregateErr([error1, error2])

    assert "Multiple errors occurred (2)" in str(aggregate)


def test_combine_all_all_ok() -> None:
    """Test that combine_all returns Ok with tuple of values when all are Ok."""
    from app.core.result import combine_all

    results = (Ok(1), Ok(2), Ok(3))
    combined = combine_all(results)

    assert isinstance(combined, Ok)
    assert combined.value == (1, 2, 3)


def test_combine_all_collects_all_errors() -> None:
    """Test that combine_all collects ALL errors."""
    from app.core.result import AggregateErr, combine_all

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="First")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Second")
    error3 = UseCaseError(type=ErrorType.UNEXPECTED, message="Third")
    results = (Err(error1), Ok(2), Err(error2), Ok(4), Err(error3))
    combined = combine_all(results)

    assert isinstance(combined, Err)
    assert isinstance(combined.error, AggregateErr)
    assert len(combined.error.exceptions) == 3
    assert combined.error.exceptions[0] is error1
    assert combined.error.exceptions[1] is error2
    assert combined.error.exceptions[2] is error3


def test_combine_all_heterogeneous_types() -> None:
    """Test that combine_all handles heterogeneous types correctly."""
    from app.core.result import Result, combine_all

    user_id: Result[int, UseCaseError] = Ok(123)
    email: Result[str, UseCaseError] = Ok("test@example.com")
    age: Result[int, UseCaseError] = Ok(25)

    combined = combine_all((user_id, email, age))

    assert isinstance(combined, Ok)
    assert combined.value == (123, "test@example.com", 25)


def test_combine_all_heterogeneous_with_errors() -> None:
    """Test that combine_all collects all errors with heterogeneous types."""
    from app.core.result import AggregateErr, Result, combine_all

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="Error 1")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Error 2")

    user_id: Result[int, UseCaseError] = Ok(123)
    email: Result[str, UseCaseError] = Err(error1)
    age: Result[int, UseCaseError] = Err(error2)

    combined = combine_all((user_id, email, age))

    assert isinstance(combined, Err)
    assert isinstance(combined.error, AggregateErr)
    assert len(combined.error.exceptions) == 2


def test_safe_decorator_wraps_exception() -> None:
    """Test that @safe decorator converts exceptions to Err."""
    from app.core.result import safe

    @safe
    def risky_function(x: int) -> int:
        if x < 0:
            raise ValueError("Negative number")
        return x * 2

    result = risky_function(-5)
    assert isinstance(result, Err)
    assert isinstance(result.error, ValueError)
    assert "Negative number" in str(result.error)


def test_safe_decorator_returns_ok() -> None:
    """Test that @safe decorator returns Ok for successful execution."""
    from app.core.result import safe

    @safe
    def safe_function(x: int) -> int:
        return x * 2

    result = safe_function(5)
    assert isinstance(result, Ok)
    assert result.value == 10


def test_ok_map_err_passes_through() -> None:
    """Test that Ok.map_err passes through unchanged without calling function."""
    result: Ok[int] = Ok(42)
    call_count = 0

    def transform_error(e: str) -> UseCaseError:
        nonlocal call_count
        call_count += 1
        return UseCaseError(type=ErrorType.UNEXPECTED, message=f"Wrapped: {e}")

    mapped = result.map_err(transform_error)

    assert isinstance(mapped, Ok)
    assert mapped.value == 42
    assert call_count == 0  # Function should not be called for Ok


def test_err_map_err_transforms_error() -> None:
    """Test that Err.map_err transforms the error value."""
    result: Err[str] = Err("original error")
    mapped = result.map_err(
        lambda e: UseCaseError(type=ErrorType.VALIDATION_ERROR, message=f"Wrapped: {e}")
    )

    assert isinstance(mapped, Err)
    assert isinstance(mapped.error, UseCaseError)
    assert mapped.error.type == ErrorType.VALIDATION_ERROR
    assert mapped.error.message == "Wrapped: original error"


def test_map_err_changes_error_type() -> None:
    """Test that map_err can change error type from str to UseCaseError."""
    result: Err[str] = Err("Not found")
    mapped = result.map_err(lambda e: UseCaseError(type=ErrorType.NOT_FOUND, message=e))

    assert isinstance(mapped, Err)
    assert isinstance(mapped.error, UseCaseError)
    assert mapped.error.type == ErrorType.NOT_FOUND
    assert mapped.error.message == "Not found"


def test_map_err_chain() -> None:
    """Test that multiple map_err calls can be chained."""
    result: Err[str] = Err("base error")
    final = (
        result.map_err(lambda e: f"Level 1: {e}")
        .map_err(lambda e: f"Level 2: {e}")
        .map_err(lambda e: f"Level 3: {e}")
    )

    assert isinstance(final, Err)
    assert final.error == "Level 3: Level 2: Level 1: base error"


def test_map_err_with_map_chain() -> None:
    """Test that map and map_err can be mixed in a chain."""
    from app.core.result import Result

    # Test with Ok - map applies, map_err passes through
    ok_result: Result[int, str] = Ok(5)
    ok_final = ok_result.map(lambda x: x * 2).map_err(lambda e: f"Error: {e}")

    assert isinstance(ok_final, Ok)
    assert ok_final.value == 10

    # Test with Err - map passes through, map_err applies
    err_result: Result[int, str] = Err("failure")
    err_final = err_result.map(lambda x: x * 2).map_err(lambda e: f"Error: {e}")

    assert isinstance(err_final, Err)
    assert err_final.error == "Error: failure"


def test_map_err_error_wrapping() -> None:
    """Test map_err for wrapping exceptions (use case from spec)."""

    def find_record(record_id: int) -> Err[KeyError]:
        """Simulate a function that returns KeyError."""
        return Err(KeyError(f"ID {record_id}"))

    # Transform KeyError to UseCaseError
    result = find_record(999).map_err(
        lambda e: UseCaseError(type=ErrorType.NOT_FOUND, message=f"Record missing: {e}")
    )

    assert isinstance(result, Err)
    assert isinstance(result.error, UseCaseError)
    assert result.error.type == ErrorType.NOT_FOUND
    assert "Record missing" in result.error.message
    assert "ID 999" in result.error.message
