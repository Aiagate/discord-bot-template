import asyncio
import logging

from injector import inject
from mediator import Request, RequestHandler
from repository import IOrderRepository, IUserRepository

logger = logging.getLogger(__name__)


class GetUserResult:
    def __init__(self, user_data: dict, order_data: dict) -> None:
        self.user = user_data
        self.order = order_data


class GetUserQuery(Request[GetUserResult]):
    def __init__(self, user_id: int, order_id: int) -> None:
        self.user_id = user_id
        self.order_id = order_id


class GetUserHandler(RequestHandler[GetUserQuery, GetUserResult]):
    @inject
    def __init__(
        self,
        user_repo: IUserRepository,
        order_repo: IOrderRepository,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo

    async def handle(self, query: GetUserQuery) -> GetUserResult:
        user = self.user_repo.get_user_by_id(query.user_id)
        order = self.order_repo.get_order_by_id(query.order_id)
        logger.debug("GetUserHandler: user=%s, order=%s", user, order)
        await asyncio.sleep(1)
        logger.debug("GetUserHandler: sleep finished")
        return GetUserResult(user, order)
