from enum import StrEnum
from datetime import datetime
from typing import Self
from fincore.signal import Signal, SignalType


class SRSignalType(StrEnum):
    SUPPORT_BREAK = "SUPPORT_BREAK"
    RESISTANCE_BREAK = "RESISTANCE_BREAK"
    SUPPORT_TOUCH = "SUPPORT_TOUCH"
    RESISTANCE_TOUCH = "RESISTANCE_TOUCH"

class SRSignal(Signal):
    def __init__(self, signal_time: datetime, sr_signal_type: SRSignalType):
        super().__init__(signal_time)
        self.sr_signal_type = sr_signal_type
        self.price = None
        self.window_size = None
        self.min_touches = None
        self.max_touches = None
        self.inner_margin = None
        self.outer_margin = None
        self.support_price = None
        self.resistance_price = None

    
    def get_signal_type(self) -> SignalType:
        return SignalType.ORDER
    

    def set_price(self, price: float)-> Self:
        self.price = price
        return self


    def set_window_size(self, window_size: int)-> Self:
        self.window_size = window_size
        return self

    
    def set_min_touches(self, min_touches: int)-> Self:
        self.min_touches = min_touches
        return self

    def set_max_touches(self, max_touches: int)-> Self:
        self.max_touches = max_touches
        return self


    def set_inner_margin(self, inner_margin: float)-> Self:
        self.inner_margin = inner_margin
        return self

    def set_outer_margin(self, outer_margin: float)-> Self:
        self.outer_margin = outer_margin
        return self
    
    def set_support_price(self, support_price: float)-> Self:
        self.support_price = support_price
        return self

    def set_resistance_price(self, resistance_price: float)-> Self:
        self.resistance_price = resistance_price
        return self


    def get_source(self):
        return 'MetaTrader5 Python API'

    
    def get_resistance_price(self):
        return self.resistance_price
    def get_support_price(self):
        return self.support_price

    def get_price(self):
        return self.price
    
    def get_window_size(self):
        return self.window_size

    def get_min_touches(self):
        return self.min_touches
    
    def get_max_touches(self):
        return self.max_touches
    
    def get_margin(self):
        return self.margin
    
    def get_sr_signal_type(self):
        return self.sr_signal_type

    
    
    def __str__(self):
        return (
            f"""
                Signal Type: {self.sr_signal_type}
                Signal Time: {self.signal_time}
                Price: {self.price}
                Window Size: {self.window_size}
                Min Touches: {self.min_touches}
                Max Touches: {self.max_touches}
                Margin: {self.margin}
            """
        )

    


