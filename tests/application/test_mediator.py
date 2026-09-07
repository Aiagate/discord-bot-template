"""Tests for the application mediator composition root."""

import pytest
from flow_res import is_ok
from injector import Injector

from app import container
from app.application.mediator import ApplicationMediator
from app.usecases.users.welcome_user import WelcomeUserCommand


@pytest.mark.anyio
async def test_container_provides_dispatching_application_mediator(
    test_db_engine: None,
) -> None:
    """The composition root dispatches the welcome user handler."""
    injector = Injector([container.configure])
    mediator = injector.get(ApplicationMediator)

    result = await mediator.send_async(WelcomeUserCommand(user_id="invalid"))

    assert is_ok(result)
    assert result.value is None
