from enum import StrEnum
from typing import TypedDict

from .order import OrderDirection


class BoxSignal(StrEnum):
    RESUME = "RESUME"
    CLOSE = "CLOSE"


class BoxSignalData(TypedDict):
    direction: OrderDirection
    signaller_name: str
