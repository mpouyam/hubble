from abc import ABC, abstractmethod
from enum import Enum
from threading import Lock
from typing import List, Self

from fincore.signaller import Signaller


class StrategyStatus(Enum):
    RUNNING = 'running'
    STOPPED = 'stopped'



class Strategy(ABC):
    def __init__(self):
        self.signallers : List[Signaller] = []
        self.status = StrategyStatus.STOPPED
        self.status_lock = Lock()


    def start(self):
        for signaller in self.signallers:
            signaller.start()
        self.set_status(StrategyStatus.RUNNING)
        self.execute()


    @abstractmethod
    def execute(self):
        pass

    def stop(self):
        for signaller in self.signallers:
            signaller.stop()
        self.set_status(StrategyStatus.STOPPED)




    def set_status(self, status: StrategyStatus)-> Self:
        with self.status_lock:
            self.status = status
        return self


    def get_status(self)-> StrategyStatus:
        with self.status_lock:
            return self.status
    def get_signallers(self):
        return self.signallers

    def add_signaller(self, signaller: Signaller):
        self.signallers.append(signaller)
        return self

    def remove_signaller(self, signaller: Signaller):
        self.signallers.remove(signaller)
        return self







