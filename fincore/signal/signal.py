from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime


class SignalType(Enum):
    ORDER = 'order'
    CHANGE_ORDER = 'change_order'
    NOP = 'no_operation'


class Signal(ABC):

    def __init__(self, signal_time: datetime):
        self.signal_time = signal_time

    @abstractmethod
    def get_source(self)-> str:
        pass

    @abstractmethod
    def get_signal_type(self)-> SignalType:
        pass









