"""Approve Join Request use case."""

import logging
from dataclasses import dataclass

from flow_med import Request, RequestHandler
from flow_res import Err, Ok, Result, is_err
from injector import inject

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.team_membership import (
    MembershipTransitionError,
    TeamMembership,
)
from app.domain.value_objects import MembershipId
from app.usecases.result import (
    ErrorType,
    UseCaseError,
    UseCaseResultError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApproveJoinRequestResult:
    """Result of approving a join request."""

    id: str
    status: str


@dataclass(frozen=True)
class ApproveJoinRequestCommand(
    Request[Result[ApproveJoinRequestResult, UseCaseResultError]]
):
    """Command to approve a join request."""

    membership_id: str


class ApproveJoinRequestHandler(
    RequestHandler[
        ApproveJoinRequestCommand,
        Result[ApproveJoinRequestResult, UseCaseResultError],
    ]
):
    """Handler for ApproveJoinRequest command."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: ApproveJoinRequestCommand
    ) -> Result[ApproveJoinRequestResult, UseCaseResultError]:
        """Approve a join request."""
        membership_id_result = MembershipId.from_primitive(request.membership_id)

        if is_err(membership_id_result):
            return Err(
                UseCaseError(
                    type=ErrorType.VALIDATION_ERROR,
                    message="Invalid Membership ID format",
                )
            )

        membership_id = membership_id_result.unwrap()

        async with self._uow:
            membership_repo = self._uow.GetRepository(TeamMembership, MembershipId)

            membership_result = await membership_repo.get_by_id(membership_id)
            if is_err(membership_result):
                return Err(membership_result.error)

            membership = membership_result.unwrap()

            try:
                membership.approve()
            except MembershipTransitionError as error:
                return Err(
                    UseCaseError(
                        type=ErrorType.VALIDATION_ERROR,
                        message=str(error),
                    )
                )

            update_result = await membership_repo.update(membership)
            if is_err(update_result):
                return Err(update_result.error)

            commit_result = await self._uow.commit()
            if is_err(commit_result):
                return Err(commit_result.error)

            return Ok(
                ApproveJoinRequestResult(
                    id=membership.id.to_primitive(),
                    status=membership.status.value,
                )
            )
