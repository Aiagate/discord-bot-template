from abc import ABC, ABCMeta, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

import container
from injector import Injector

R = TypeVar("R")
T = TypeVar("T")


class AutoRegisterMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        class_dict: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcs, name, bases, class_dict)

        if name == "RequestHandler":
            return cls

        # RequestHandler の自動登録
        if "handle" in class_dict and not hasattr(cls, "__abstractmethods__"):
            # Request の型を取得
            request_type = cls.__orig_bases__[0].__args__[0]
            # Mediator に登録
            Mediator.register(request_type, cls)

        return cls


class CombinedMeta(ABCMeta, AutoRegisterMeta):
    pass


class RequestHandler(ABC, Generic[T, R], metaclass=CombinedMeta):
    @abstractmethod
    def handle(self, request: T) -> R:
        pass


class Mediator:
    _request_handlers: ClassVar[dict] = {}

    @classmethod
    def send(cls, request: T) -> R:
        handler_provider = cls._request_handlers.get(type(request))
        if not handler_provider:
            raise HandlerNotFoundError(request)

        injector = Injector([container.configure])

        handler = injector.get(handler_provider)
        return handler.handle(request)

    @classmethod
    def register(cls, request_type: T, handler_type: R) -> None:
        """リクエストとハンドラーの登録"""
        cls._request_handlers[request_type] = handler_type


class MediatorError(Exception):
    pass


class HandlerNotFoundError(MediatorError):
    def __init__(self, target: type) -> None:
        super().__init__(
            f"Handler not found for request type: {type(target)}",
        )


__all__ = [
    "HandlerNotFoundError",
    "Mediator",
    "RequestHandler",
]
