from abc import ABC, abstractmethod

from fincore.signal import Signal


class SignalHandler(ABC):
    @abstractmethod
    def handle_signal(self, signal: Signal):
        pass
