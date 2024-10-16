import threading
from abc import abstractmethod, ABC
from enum import StrEnum
from typing import Self

from fincore.signal_handler import SignalHandler


class SignallerStatus(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class Signaller(ABC):

    @abstractmethod
    def get_signaller_name(self):
        pass

    def __init__(self):
        self.thread = threading.Thread(target=self.process, daemon=True)
        self.status_lock = threading.Lock()
        self.status = SignallerStatus.STOPPED
        self.ready_lock = threading.Lock()
        self.ready = False

    def start(self):
        self.thread.start()
        while not self.is_ready():
            pass

    def set_ready(self, ready: bool):
        with self.ready_lock:
            self.ready = ready
        self.set_status(SignallerStatus.RUNNING)

    @abstractmethod
    def subscribe_handler(self, handler: SignalHandler) -> Self:
        pass

    @abstractmethod
    def unsubscribe_handler(self, handler: SignalHandler) -> Self:
        pass

    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def is_ready(self) -> bool:
        with self.ready_lock:
            return self.ready

    def set_status(self, status: SignallerStatus):
        with self.status_lock:
            self.status = status

    def get_status(self) -> SignallerStatus:
        with self.status_lock:
            return self.status
