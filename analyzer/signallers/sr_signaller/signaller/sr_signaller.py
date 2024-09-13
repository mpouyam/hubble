import threading
from typing import Self
from fincore.signal_handler import SignalHandler
from fincore.signaller import Signaller, SignallerStatus
from platform import Platform


class SRSignallerConfig:
    def __init__(
            self,
            symbol: str,
            inner_margin: float,
            outer_margin: float,
            min_touches: int,
            candle_frame: int,
            candle_count: int
    ):
        self.symbol = symbol
        self.inner_margin = inner_margin
        self.outer_margin = outer_margin
        self.min_touches = min_touches
        self.candle_frame = candle_frame
        self.candle_count = candle_count

    def get_inner_margin(self)-> float:
        return self.inner_margin

    def get_outer_margin(self)-> float:
        return self.outer_margin

    def get_min_touches(self)-> int:
        return self.min_touches

    def get_candle_frame(self)-> int:
        return self.candle_frame

    def get_candle_count(self)-> int:
        return self.candle_count


class SupportResistanceSignaller(Signaller):


    def subscribe_handler(self, handler: SignalHandler) -> Self:
        pass

    def unsubscribe_handler(self, handler: SignalHandler) -> Self:
        pass

    def stop(self):
        self.set_status(SignallerStatus.STOPPED)

    def is_ready(self) -> bool:
        with self.ready_lock:
            return self.ready


    def process(self):
        while self.get_status() == SignallerStatus.RUNNING:
            pass

    def __init__(self, config: SRSignallerConfig, platform: Platform):
        super().__init__()
        self.config = config
        self.ready = False
        self.platform = platform
        self.ready_lock = threading.Lock()


    def set_ready(self, ready: bool):
        with self.ready_lock:
            self.ready = ready


    def get_signaller_name(self)-> str:
        return 'SR Signaller'

    


        


         

    

    