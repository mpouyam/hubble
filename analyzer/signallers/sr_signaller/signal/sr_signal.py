from enum import StrEnum
from datetime import datetime
from typing import Self
from fincore.signal import Signal, SignalType


class SRSignalType(StrEnum):
    SUPPORT_BREAK = "SUPPORT_BREAK"
    RESISTANCE_BREAK = "RESISTANCE_BREAK"

class SRSignal(Signal):
    def __init__(self, signal_time: datetime, sr_signal_type: SRSignalType , name: str):
        super().__init__(signal_time)
        self.name = name
        self.sr_signal_type = sr_signal_type
        self.close_price = None
        self.window_size = None
        self.min_touches = None
        self.actual_touches = None
        self.inner_margin = None
        self.outer_margin = None
        self.support_price = None
        self.resistance_price = None

    
    def get_signal_type(self) -> SignalType:
        return SignalType.ORDER
    

    def set_close_price(self, price: float)-> Self:
        self.close_price = price
        return self


    def set_window_size(self, window_size: int)-> Self:
        self.window_size = window_size
        return self

    
    def set_min_touches(self, min_touches: int)-> Self:
        self.min_touches = min_touches
        return self

    def set_actual_touches(self, actual_touches: int)-> Self:
        self.actual_touches = actual_touches
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
    
    def get_name(self):
            return self.name
    
    def get_resistance_price(self):
        return self.resistance_price
    def get_support_price(self):
        return self.support_price

    def get_close_price(self):
        return self.close_price
    
    def get_window_size(self):
        return self.window_size

    def get_min_touches(self):
        return self.min_touches
    
    def get_actual_touches(self):
        return self.actual_touches
    
    def get_inner_margin(self):
        return self.inner_margin

    def get_outer_margin(self):
        return self.outer_margin
    
    def get_sr_signal_type(self):
        return self.sr_signal_type

    
    
    def __str__(self):
        return (
            f"""
                Signal Type: {self.sr_signal_type}
                Signal Time: {self.signal_time}
                Close Price: {self.close_price}
                Window Size: {self.window_size}
                Min Touches: {self.min_touches}
                Actual Touches: {self.actual_touches}
                Inner Margin: {self.inner_margin}
                Outer Margin: {self.outer_margin}
            """
        )

    


