
from trading_platform import Platform
from strategies import Signal
from threading import Lock
from enum import StrEnum


class CandleRangeSignallerState(StrEnum):
    INIT = 'init'
    RUNNING = 'running'
    STOPPED = 'stopped'

class CandleRangeSignallerConfig:
    pass 


class CandleRangeSignaller: 
    def __init__(
        self,
        platform: Platform,
        cb: callable[Signal],
        config: CandleRangeSignallerConfig
    ): 
        
        self.platform = platform
        self.state = CandleRangeSignallerState.INIT
        self.state_lock : Lock = Lock()
        self.cb = cb
        self.config = config
    

    def set_state(self, new_state: CandleRangeSignallerState):
        with self.state_lock:
            self.state = new_state 

    def stop(self) ->bool: 
        if self.get_state() == CandleRangeSignallerState.INIT:
            return False
        self.set_state(CandleRangeSignallerState.STOPPED)
        return True
    

    def get_state(self) -> CandleRangeSignallerState:
        return self.state
        
    def start(self) -> None:
        if self.get_state() != CandleRangeSignaller.RUNNING:
            self.set_state(CandleRangeSignallerState.RUNNING)
        while(self.get_state() == CandleRangeSignallerState.RUNNING):
            # DO THE Work 
        