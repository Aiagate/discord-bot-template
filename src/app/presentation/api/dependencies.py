"""FastAPI dependencies for presentation-layer services."""

from typing import cast

from fastapi import Request

from app.application.mediator import ApplicationMediator


def get_mediator(request: Request) -> ApplicationMediator:
    """Return the mediator created by the application's composition root."""
    return cast(ApplicationMediator, request.app.state.mediator)


__all__ = ["get_mediator"]
