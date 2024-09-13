#
# from trading_platform import Platform
# from strategies import Signal
# from threading import Lock, Thread
# from enum import StrEnum
# from datetime import datetime
# import time
# from typing import Callable
# import pytz
#
# class CandleRangeSignallerState(StrEnum):
#     INIT = 'init'
#     RUNNING = 'running'
#     STOPPED = 'stopped'
#
# class CandleRangeSignallerConfig:
#     def __init__(self):
#         self.count: int  = 3
#
#     def set_count(self, count: int) -> 'CandleRangeSignallerConfig':
#         self.count = count
#         return self
#
#     def get_count(self) -> int:
#         return self.count
#
#
# class CandleRangeSignaller:
#     def __init__(
#         self,
#         symbol: str,
#         platform: Platform,
#         cb: Callable[[Signal], None],
#         config: CandleRangeSignallerConfig
#     ):
#
#         self.platform = platform
#         self.state = CandleRangeSignallerState.INIT
#         self.symbol = symbol
#         self.state_lock : Lock = Lock()
#         self.cb = cb
#         self.config = config
#         self.thread : Thread | None = None
#
#
#     def set_state(self, new_state: CandleRangeSignallerState):
#         with self.state_lock:
#             self.state = new_state
#
#     def stop(self) ->bool:
#         if self.get_state() == CandleRangeSignallerState.INIT:
#             return False
#         self.set_state(CandleRangeSignallerState.STOPPED)
#         self.thread.join()
#         self.thread = None
#         return True
#
#
#     def get_state(self) -> CandleRangeSignallerState:
#         return self.state
#
#
#     def start(self) -> None:
#         if self.get_state() != CandleRangeSignallerState.RUNNING:
#             self.set_state(CandleRangeSignallerState.RUNNING)
#             if self.thread is not None:
#                 self.thread.join()
#             self.thread = Thread(target=self.check_and_call, daemon=True)
#             self.thread.start()
#
#
#     def check_and_call(self) -> None:
#         last_candle_time = -1
#         count =  self.config.get_count()
#         while(self.get_state() == CandleRangeSignallerState.RUNNING):
#             candles = self.platform.get_candles_from(
#                 self.symbol, 1, datetime.now(), count
#             )
#             new_last_candle_time = candles[-1]['time']
#
#             if len(candles) >= count and new_last_candle_time > last_candle_time:
#                 if self.is_ascending(candles, count):
#                     self.cb(Signal.ON)
#                 last_candle_time = new_last_candle_time
#             time.sleep(1)
#
#     def is_ascending(self, candles, count):
#         if len(candles) < count:
#             return False
#         if candles[0]['open'] >= candles[0]['close']:
#             return False
#         closes = [candle['close'] for candle in candles]
#         if closes == sorted(closes):
#             return True
