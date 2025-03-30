import injector
from repository import (
    IOrderRepository,
    IUserRepository,
    SQLiteOrderRepository,
    SQLiteUserRepository,
)


def configure(binder: injector.Binder) -> None:
    binder.bind(IUserRepository, SQLiteUserRepository())
    binder.bind(IOrderRepository, SQLiteOrderRepository())
