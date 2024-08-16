from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from strategy.order import OrderManager


class OrderSignal(StrEnum):
    CLOSE = "CLOSE"


class OrderStatus(StrEnum):
    SL = "SL"
    TP = "TP"
    CLOSED = "CLOSED"
    NOTHING = "NOTHING"


class OrderErrorStatus(StrEnum):
    NONE = "NONE"
    PLACING = "PLACING"
    MODIFYING = "MODIFYING"
    CLOSING = "CLOSING"


class OrderDirection(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class OrderRecipes:
    direction: OrderDirection
    symbol: str
    unit: float
    volume: float
    sl: float
    tp: float


@dataclass
class Order:
    symbol: str
    pip_unit: float
    status: OrderStatus
    direction: OrderDirection
    volume: float
    tp_limit: float
    sl_limit: float
    ticket: Optional[int]
    price: Optional[float]
    tp_price: Optional[float]
    sl_price: Optional[float]
    started_at: Optional[str]
    ended_at: Optional[str]
    error: Optional[str]
    error_status: OrderErrorStatus


class OrderState(ABC):
    _order_manager: OrderManager

    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager

    @order_manager.setter
    def order_manager(self, order_manager: OrderManager) -> None:
        self._order_manager = order_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: OrderSignal) -> None:
        pass

    @abstractmethod
    def get_prototype(self) -> Order:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass
