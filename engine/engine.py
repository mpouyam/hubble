import time
from datetime import datetime, timedelta
import threading
import math
import pytz


class TickListener:

    def on_tick_concurrent(self, tick):
        thread = threading.Thread(target = self.on_tick, args=(tick))
        thread.start()

    def get_symbol(self):
        pass 

    def on_tick(
        self,
        tick
    ):
        pass


class EngineConfig:
    def __init__(
        self,
        config_dict: dict = None,
    ):
        self.symbol = config_dict["symbol"]
        self.max_subs = config_dict["max_subs"]
        self.max_stored_ticks = config_dict["max_stored_ticks"]
        self.period = config_dict["period"]
    
    
    def set_max_stored_ticks(self, max_stored_ticks):
        self.max_stored_ticks = max_stored_ticks
        return self
    
    def get_max_stored_ticks(self):
        return self.max_stored_ticks
    
    def set_max_subs(self, max_subs):
        self.max_subs = max_subs
        return self
    
    def get_max_subs(self):
        return self.max_subs
    
    def set_symbol(self, symbol):
        self.symbol = symbol
        return symbol
    
    def get_symbol(self):
        return self.symbol 

    def set_period(self, period):
        self.period = period
        return self 
    
    def get_period(self):
        return self.period



class Engine:
    def __init__(self, config: EngineConfig, mt5):
        self.config = config
        self.mt5 = mt5
        self.ticks = []
        self.tick_listeners = []
        self._state = "initialized"


    def add_tick_listener(self, listener):
        if listener.get_symbol() != self.config.get_symbol():
            raise Exception("Subscriber symbol is not consistent with engine's working symbol.")
        self.tick_listeners.append(listener)

    def remove_tick_listener(self, listener):
        self.tick_listeners.remove(listener)

    def set_symbol(self, symbol: str):
        self.symbol = symbol
    
    def start(self):
        self._state = "running"
        symbol = self.config.get_symbol()
        # timezone = pytz.timezone("Etc/UTC")
        period = self.config.get_period()
        # last_update = datetime.now(timezone) - timedelta(minutes = 1)
        while True:
            tick_info = self.mt5.symbol_info_tick(symbol)

            timestamp = tick_info.time
            bid = tick_info.bid
            ask = tick_info.ask
            volume = tick_info.volume
            tick = (timestamp , bid , ask , volume)
            # new_ticks = self.mt5.copy_ticks_range(
            #     self.config.get_symbol(),
            #     last_update,
            #     datetime.now(timezone),
            #     self.mt5.COPY_TICKS_ALL
            # )
            # last_update = datetime.now(timezone) - timedelta(seconds=0.1)
            # for tick in new_ticks:
            result = self.add_to_ticks(tick)
            if result:
                self.tick(result)
        
            # print(new_ticks)
            # print(self.ticks)
            time.sleep(period)


            
    def add_to_ticks(self, tick):
        if len(self.ticks) + 1 == self.config.get_max_stored_ticks():
            self.ticks = self.ticks[math.floor(0.3*self.config.get_max_stored_ticks()):]
        if tick not in self.ticks:
            self.ticks.append(tick)
            return tick
        return None 

    
    def tick(self, tick):
        for listener in self.tick_listeners:
            listener.on_tick(tick)


