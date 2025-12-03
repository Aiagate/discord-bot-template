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


def test_err_unwrap_raises_exception() -> None:
    """Test that Err.unwrap raises the error."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="User not found")
    result: Err[UseCaseError] = Err(error)

    with pytest.raises(UseCaseError) as exc_info:
        result.unwrap()

    assert exc_info.value is error
    assert str(exc_info.value) == "User not found"


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


def test_map_unwrap_chain_with_err() -> None:
    """Test that map and unwrap chain raises on Err."""
    error = UseCaseError(type=ErrorType.UNEXPECTED, message="Something went wrong")
    result: Err[UseCaseError] = Err(error)

    with pytest.raises(UseCaseError) as exc_info:
        result.map(lambda x: x * 2).unwrap()

    assert exc_info.value is error


def test_err_unwrap_with_non_exception() -> None:
    """Test that Err.unwrap raises RuntimeError for non-Exception errors."""
    result: Err[str] = Err("Not an exception")

    with pytest.raises(RuntimeError) as exc_info:
        result.unwrap()

    assert "Error: Not an exception" in str(exc_info.value)


def test_usecase_error_str() -> None:
    """Test that UseCaseError.__str__ returns the message."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Resource not found")

    assert str(error) == "Resource not found"


def test_combine_all_ok() -> None:
    """Test that combine returns Ok with tuple of values when all are Ok."""
    from app.core.result import combine

    results = [Ok(1), Ok(2), Ok(3)]
    combined = combine(results)

    assert isinstance(combined, Ok)
    assert combined.value == [1, 2, 3]


def test_combine_with_err() -> None:
    """Test that combine returns first Err when any result is Err."""
    from app.core.result import combine

    error1 = UseCaseError(type=ErrorType.NOT_FOUND, message="First error")
    error2 = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Second error")
    results = [Ok(1), Err(error1), Ok(3), Err(error2)]
    combined = combine(results)

    assert isinstance(combined, Err)
    assert combined.error is error1


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
