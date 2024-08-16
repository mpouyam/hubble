from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


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


