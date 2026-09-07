"""Tests for repository-to-use-case error classification."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from flow_res import Err, Ok, is_err
from ulid import ULID

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.team_membership import TeamMembership
from app.domain.repositories import RepositoryError, RepositoryErrorType
from app.domain.value_objects import TeamId, UserId
from app.usecases.error_mapping import classify_error
from app.usecases.memberships.change_role import (
    ChangeRoleCommand,
    ChangeRoleHandler,
)
from app.usecases.memberships.request_join_team import (
    RequestJoinTeamCommand,
    RequestJoinTeamHandler,
)
from app.usecases.result import ErrorType, UseCaseError
from app.usecases.teams.get_team import GetTeamHandler, GetTeamQuery


def _mock_uow(repository: object) -> IUnitOfWork:
    """Create a unit-of-work mock for one repository."""
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_uow.GetRepository.return_value = repository
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    return cast(IUnitOfWork, mock_uow)


@pytest.mark.parametrize(
    ("repository_type", "use_case_type"),
    (
        (RepositoryErrorType.NOT_FOUND, ErrorType.NOT_FOUND),
        (RepositoryErrorType.ALREADY_EXISTS, ErrorType.CONFLICT),
        (RepositoryErrorType.VERSION_CONFLICT, ErrorType.CONCURRENCY_CONFLICT),
        (RepositoryErrorType.UNEXPECTED, ErrorType.UNEXPECTED),
    ),
)
def test_classify_error_maps_persistence_failures(
    repository_type: RepositoryErrorType,
    use_case_type: ErrorType,
) -> None:
    """Map each repository error to the corresponding application category."""
    result = classify_error(
        RepositoryError(type=repository_type, message="storage detail")
    )

    assert result.type is use_case_type
    assert result.message == "storage detail"
    assert result.display_message != "storage detail"


@pytest.mark.anyio
async def test_get_team_preserves_unexpected_repository_errors() -> None:
    """A failed read remains internal until the application boundary."""
    repository_error = RepositoryError(
        type=RepositoryErrorType.UNEXPECTED,
        message="database unavailable",
    )
    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=Err(repository_error))
    handler = GetTeamHandler(_mock_uow(repository))

    result = await handler.handle(GetTeamQuery(id=str(ULID())))

    assert is_err(result)
    assert result.error is repository_error
    assert result.error.type is RepositoryErrorType.UNEXPECTED
    assert result.error.message == "database unavailable"


@pytest.mark.anyio
async def test_request_join_preserves_duplicate_repository_error() -> None:
    """A duplicate membership remains internal until the application boundary."""
    team_repository = MagicMock()
    team_repository.get_by_id = AsyncMock(return_value=Ok(None))
    user_repository = MagicMock()
    user_repository.get_by_id = AsyncMock(return_value=Ok(None))
    membership_repository = MagicMock()
    membership_repository.add = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.ALREADY_EXISTS,
                message="unique constraint failed",
            )
        )
    )

    uow = _mock_uow(team_repository)
    uow.GetRepository = MagicMock(
        side_effect=[team_repository, user_repository, membership_repository]
    )
    handler = RequestJoinTeamHandler(uow)

    result = await handler.handle(
        RequestJoinTeamCommand(team_id=str(ULID()), user_id=str(ULID()))
    )

    assert is_err(result)
    assert result.error.type is RepositoryErrorType.ALREADY_EXISTS
    assert result.error.message == "unique constraint failed"


@pytest.mark.anyio
async def test_change_role_preserves_version_conflict() -> None:
    """An optimistic-locking failure remains internal until the boundary."""
    membership = TeamMembership.join(
        team_id=TeamId.generate().expect("valid team id"),
        user_id=UserId.generate().expect("valid user id"),
    )
    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=Ok(membership))
    repository.update = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.VERSION_CONFLICT,
                message="stale version",
            )
        )
    )
    handler = ChangeRoleHandler(_mock_uow(repository))

    result = await handler.handle(
        ChangeRoleCommand(
            membership_id=membership.id.to_primitive(),
            new_role="ADMIN",
        )
    )

    assert is_err(result)
    assert result.error.type is RepositoryErrorType.VERSION_CONFLICT
    assert result.error.message == "stale version"


def test_classify_error_preserves_existing_usecase_errors() -> None:
    """Boundary mapping does not reclassify validation errors."""
    usecase_error = UseCaseError(
        type=ErrorType.VALIDATION_ERROR,
        message="Invalid input",
    )

    assert classify_error(usecase_error) is usecase_error


def test_classify_error_maps_repository_errors_once() -> None:
    """Boundary mapping translates persistence categories at the edge."""
    result = classify_error(
        RepositoryError(
            type=RepositoryErrorType.ALREADY_EXISTS,
            message="unique constraint failed",
        )
    )

    assert result.type is ErrorType.CONFLICT
    assert result.message == "unique constraint failed"
