import time
from datetime import datetime, timedelta
from trading_platform import Platform 
import threading
import math


class TickListener:
    def on_tick_concurrent(self, tick):
        thread = threading.Thread(target = self.on_tick, args=(tick,))
        thread.start()
        return thread

    def get_symbol(self):
        pass 

    def on_tick(
        self,
        tick
    ):
        pass


class PublisherConfig:
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



class Publisher:
    def __init__(self, config: PublisherConfig, platform: Platform):
        self.config = config
        self.platform = platform
        self.ticks = []
        self.tick_listeners = []
        self.last_tick = None
        self.producer_thread = None
        self.consumer_thread = None
        self.state_lock = threading.Lock()
        self.ticks_lock = threading.Lock()
        self._state = "initialized"


    def add_tick_listener(self, listener):
        if listener.get_symbol() != self.config.get_symbol():
            raise Exception("Subscriber symbol is not consistent with engine's working symbol.")
        if len(self.tick_listeners) + 1 > self.config.get_max_subs():
            raise Exception("Max number of subscribers reached.")
        self.tick_listeners.append(listener)


    def remove_tick_listener(self, listener):
        self.tick_listeners.remove(listener)

    def start(self):
        with self.state_lock:
            self._state = "running"
        symbol = self.config.get_symbol()
        period = self.config.get_period()
        self.consumer_thread = threading.Thread(target=self.consume, args=(period,), daemon=True)
        self.producer_thread = threading.Thread(target=self.produce, args=(symbol, period,), daemon=True)
        self.consumer_thread.start()
        self.producer_thread.start()

    def produce(self, symbol, period):
            state = None
            with self.state_lock:
                state = self._state
            while state == "running":
                tick = self.platform.get_symbol_info(symbol)
                with self.ticks_lock:
                    self.add_to_ticks(tick)
                time.sleep(period)
                with self.state_lock:
                    state = self._state
    
    def consume(self, period):
            state = None
            with self.state_lock:
                state = self._state
            while state == "running":
                tick = None 
                with self.ticks_lock:
                    if len(self.ticks) > 0:
                        tick = self.ticks.pop(0)
                        self.tick(tick)                        
                time.sleep(period)
                with self.state_lock:
                    state = self._state


    def stop(self):
        with self.state_lock:
            self._state = "stopped"
        self.consumer_thread.join()
        self.producer_thread.join()
        return 1

    def add_to_ticks(self, tick):
        if len(self.ticks) + 1 == self.config.get_max_stored_ticks():
            self.ticks = self.ticks[math.floor(0.3*self.config.get_max_stored_ticks()):]
        if self.last_tick == None or (tick[1:] != self.last_tick[1:]) :
            self.last_tick = tick
            self.ticks.append(tick)
            return tick
        return None 

    
    def tick(self, tick):
        threads = []
        for listener in self.tick_listeners:
            threads.append(listener.on_tick_concurrent(tick))
        for thread in threads:
            thread.join()


