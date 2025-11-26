"""Tests for the dependency injection container."""

import pytest
from injector import Injector

from app import container
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.repository import IUnitOfWork


@pytest.mark.anyio
async def test_di_container_bindings(test_db_engine: None) -> None:
    """Test that the DI container is configured correctly."""
    injector = Injector([container.configure])

    # Test that requesting the IUnitOfWork interface returns the correct implementation
    uow_instance = injector.get(IUnitOfWork)

    assert isinstance(uow_instance, SQLAlchemyUnitOfWork)
