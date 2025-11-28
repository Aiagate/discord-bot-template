"""Tests for the dependency injection container."""

import pytest
from injector import Injector

from app import container
from app.domain.repositories import IUnitOfWork
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork


@pytest.mark.anyio
async def test_di_container_bindings(test_db_engine: None) -> None:
    """Test that the DI container is configured correctly."""
    injector = Injector([container.configure])

    # Test that requesting the IUnitOfWork interface returns the correct implementation
    uow_instance = injector.get(IUnitOfWork)

    assert isinstance(uow_instance, SQLAlchemyUnitOfWork)
