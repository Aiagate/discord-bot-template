from injector import inject
from mediator import Mediator, RequestHandler
from repository import IOrderRepository, IUserRepository


class GetUserQuery:
    def __init__(self, user_id: int, order_id: int) -> None:
        self.user_id = user_id
        self.order_id = order_id


class GetUsersQuery:
    def __init__(self, user_id: int, order_id: int) -> None:
        self.user_id = user_id
        self.order_id = order_id


class GetUserResult:
    def __init__(self, user_data: dict, order_data: dict) -> None:
        self.user = user_data
        self.order = order_data


class GetUserHandler(RequestHandler[GetUserQuery, GetUserResult]):
    @inject
    def __init__(
        self,
        user_repo: IUserRepository,
        order_repo: IOrderRepository,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo

    def handle(self, query: GetUserQuery) -> GetUserResult:
        user = self.user_repo.get_user_by_id(query.user_id)
        order = self.order_repo.get_order_by_id(query.order_id)
        return GetUserResult(user, order)


# Mediator を使用してリクエストを送信
query = GetUserQuery(user_id=1, order_id=100)
result = Mediator.send(query)
print(result.user)
query2 = GetUsersQuery(user_id=1, order_id=100)
result2 = Mediator.send(query2)
