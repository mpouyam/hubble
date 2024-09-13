import threading
from abc import abstractmethod, ABC
from enum import StrEnum
from typing import Self

from finwave.fincore.signal_handler import SignalHandler


class SignallerStatus(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"



class Signaller(ABC):

    @abstractmethod
    def get_signaller_name(self):
        pass


    def __init__(self):
        self.thread = threading.Thread(target=self.process)
        self.status_lock = threading.Lock()
        self.status = SignallerStatus.STOPPED



    def start(self):
        self.thread.start()
        while not self.is_ready():
            pass
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


    @abstractmethod
    def is_ready(self)-> bool:
        pass


    def set_status(self, status: SignallerStatus):
        with self.status_lock:
            self.status = status

    def get_status(self) -> SignallerStatus:
        with self.status_lock:
            return self.status


