from abc import ABC, abstractmethod


class IUserRepository(ABC):
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> dict:
        pass


class IOrderRepository(ABC):
    @abstractmethod
    def get_order_by_id(self, order_id: int) -> dict:
        pass


class SQLiteUserRepository(IUserRepository):
    def get_user_by_id(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Alice"}


class SQLiteOrderRepository(IOrderRepository):
    def get_order_by_id(self, order_id: int) -> dict:
        return {"id": order_id, "product": "Laptop"}
