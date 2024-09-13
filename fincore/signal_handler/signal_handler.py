from abc import ABC, abstractmethod

from finwave.fincore.signal import Signal


class SignalHandler(ABC):
    @abstractmethod
    def handle_signal(self, signal: Signal):
        pass
