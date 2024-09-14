from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypedDict

from strategy import BoxManager
from internal_types import OrderDirection


class BoxSignal(StrEnum):
    RESUME = "RESUME"
    CLOSE = "CLOSE"


class BoxSignalData(TypedDict):
    direction: OrderDirection


class BoxState(ABC):
    _box_manager: BoxManager

    @property
    def box_manager(self) -> BoxManager:
        return self._box_manager

    @box_manager.setter
    def box_manager(self, box_manager: BoxManager) -> None:
        self._box_manager = box_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass
