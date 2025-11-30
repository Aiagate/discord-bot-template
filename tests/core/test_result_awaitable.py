"""Tests for ResultAwaitable type."""

import pytest

from app.core.result import Err, Ok, Result, ResultAwaitable
from app.usecases.result import ErrorType, UseCaseError


async def async_double(x: int) -> Result[int, UseCaseError]:
    """Helper function that returns Ok with doubled value."""
    return Ok(x * 2)


async def async_add_ten(x: int) -> Result[int, UseCaseError]:
    """Helper function that returns Ok with value plus 10."""
    return Ok(x + 10)


@pytest.mark.anyio
async def test_result_awaitable_await_ok() -> None:
    """Test that ResultAwaitable can be awaited to get Result."""

    async def get_result() -> Ok[int]:
        return Ok(42)

    awaitable = ResultAwaitable(get_result())
    result = await awaitable

    assert isinstance(result, Ok)
    assert result.value == 42


@pytest.mark.anyio
async def test_result_awaitable_await_err() -> None:
    """Test that ResultAwaitable can be awaited to get Err."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")

    async def get_result() -> Err[UseCaseError]:
        return Err(error)

    awaitable = ResultAwaitable(get_result())
    result = await awaitable

    assert isinstance(result, Err)
    assert result.error is error


@pytest.mark.anyio
async def test_result_awaitable_map_ok() -> None:
    """Test that ResultAwaitable.map transforms Ok value."""

    async def get_result() -> Ok[int]:
        return Ok(5)

    result = await ResultAwaitable(get_result()).map(lambda x: x * 2)  # type: ignore[arg-type, return-value]

    assert isinstance(result, Ok)
    assert result.value == 10


@pytest.mark.anyio
async def test_result_awaitable_map_err() -> None:
    """Test that ResultAwaitable.map passes through Err."""
    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Invalid")

    async def get_result() -> Err[UseCaseError]:
        return Err(error)

    result = await ResultAwaitable(get_result()).map(lambda x: x * 2)  # type: ignore[arg-type, return-value]

    assert isinstance(result, Err)
    assert result.error is error


@pytest.mark.anyio
async def test_result_awaitable_map_chain() -> None:
    """Test that multiple map calls can be chained."""

    async def get_result() -> Ok[int]:
        return Ok(5)

    result = await (
        ResultAwaitable(get_result())
        .map(lambda x: x * 2)
        .map(lambda x: x + 3)
        .map(lambda x: f"Result: {x}")
    )

    assert isinstance(result, Ok)
    assert result.value == "Result: 13"


@pytest.mark.anyio
async def test_result_awaitable_unwrap_ok() -> None:
    """Test that unwrap returns value for Ok."""

    async def get_result() -> Ok[int]:
        return Ok(42)

    value = await ResultAwaitable(get_result()).unwrap()

    assert value == 42


@pytest.mark.anyio
async def test_result_awaitable_unwrap_err() -> None:
    """Test that unwrap raises exception for Err."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")

    async def get_result() -> Err[UseCaseError]:
        return Err(error)

    with pytest.raises(UseCaseError) as exc_info:
        await ResultAwaitable(get_result()).unwrap()

    assert exc_info.value is error


@pytest.mark.anyio
async def test_result_awaitable_full_chain() -> None:
    """Test complete chain: map -> map -> unwrap."""

    async def get_result() -> Ok[int]:
        return Ok(10)

    value = await (
        ResultAwaitable(get_result()).map(lambda x: x * 2).map(lambda x: x + 5).unwrap()
    )

    assert value == 25


@pytest.mark.anyio
async def test_result_awaitable_full_chain_with_err() -> None:
    """Test complete chain with Err raises exception."""
    error = UseCaseError(type=ErrorType.UNEXPECTED, message="Error")

    async def get_result() -> Err[UseCaseError]:
        return Err(error)

    with pytest.raises(UseCaseError) as exc_info:
        await ResultAwaitable(get_result()).map(lambda x: x * 2).unwrap()  # type: ignore[arg-type, return-value]

    assert exc_info.value is error


@pytest.mark.anyio
async def test_result_awaitable_and_then_ok() -> None:
    """Test that ResultAwaitable.and_then applies function for Ok."""

    async def get_initial() -> Result[int, UseCaseError]:
        return Ok(5)

    result = ResultAwaitable(get_initial())
    final = await result.and_then(async_double)

    assert isinstance(final, Ok)
    assert final.value == 10


@pytest.mark.anyio
async def test_result_awaitable_and_then_err() -> None:
    """Test that ResultAwaitable.and_then passes through Err."""
    error = UseCaseError(type=ErrorType.NOT_FOUND, message="Not found")

    async def get_error() -> Result[int, UseCaseError]:
        return Err(error)

    result = ResultAwaitable(get_error())
    final = await result.and_then(async_double)

    assert isinstance(final, Err)
    assert final.error is error


@pytest.mark.anyio
async def test_result_awaitable_and_then_chain() -> None:
    """Test that multiple and_then calls can be chained."""

    async def get_initial() -> Result[int, UseCaseError]:
        return Ok(2)

    result = ResultAwaitable(get_initial())
    final = await result.and_then(async_double).and_then(async_add_ten)

    assert isinstance(final, Ok)
    assert final.value == 14  # (2 * 2) + 10


@pytest.mark.anyio
async def test_result_awaitable_and_then_with_map() -> None:
    """Test that and_then and map can be combined."""

    async def get_initial() -> Result[int, UseCaseError]:
        return Ok(5)

    result = ResultAwaitable(get_initial())
    final_value = await (
        result.and_then(async_double)
        .map(lambda x: x + 5)
        .and_then(async_add_ten)
        .unwrap()
    )

    assert final_value == 25  # ((5 * 2) + 5) + 10


@pytest.mark.anyio
async def test_result_awaitable_and_then_error_propagation() -> None:
    """Test that error in and_then chain stops further processing."""

    async def get_initial() -> Result[int, UseCaseError]:
        return Ok(5)

    error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message="Validation failed")

    async def returns_error(x: int) -> Result[int, UseCaseError]:
        return Err(error)

    result = ResultAwaitable(get_initial())
    final = await (
        result.and_then(async_double)
        .and_then(returns_error)
        .and_then(async_add_ten)  # Should not execute
    )

    assert isinstance(final, Err)
    assert final.error is error
