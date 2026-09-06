"""Capability contract for entities that cannot be updated or deleted."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IAppendOnly(Protocol):
    """Identify an entity whose persistence operations are append-only."""

    @property
    def is_append_only(self) -> bool:
        """Return whether the entity supports only insertion."""
        ...
