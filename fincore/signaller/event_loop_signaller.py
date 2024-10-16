from abc import abstractmethod
from fincore.signaller import Signaller
import asyncio

from fincore.signaller.signaller import SignallerStatus


class EventLoopSignaller(Signaller):

    def __init__(self):
        super().__init__()
        self.event_loop = asyncio.new_event_loop()



    def start(self):
        self.thread.start()
        while not self.is_ready():
            pass


    def get_event_loop(self)-> asyncio.AbstractEventLoop:
        return self.event_loop


    @abstractmethod
    def get_signaller_name(self):
        pass


    @abstractmethod
    def stop(self):
        pass