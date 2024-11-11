# from .trading_platform.platform import Platform
# import MetaTrader5 as mt5


# class PlatformMock(Platform):
#     def __init__(self, platform_config , symbol: str, start_date: datetime, tick_count: int = 1000, candle_count: int = 1000) -> None:
#         self.symbol = symbol
#         self.tick_count = tick_count
#         self.candle_count = candle_count
#         self.start_date = start_date
#         self.current_candle_index = 0
#         self.current_tick_index = 0
#         self.tick_pointer_within_candle = 0

#         self.candles_data = self._load_candle_data()
#         self.ticks_data = self._load_tick_data(self.candles_data[self.current_candle_index].time)
#         self._prepare_tick_buffer()
#         super().initialize(platform_config)

#     def get_candles(self, symbol: str, timeframe: str, start_pos: int, count: int) -> List[Candle]:
#         end_pos = self.current_candle_index + count
#         if end_pos > len(self.candles_data):
#             raise RuntimeError("Insufficient candle data for requested range.")
#         result_candles = self.candles_data[self.current_candle_index:end_pos]
#         self.current_candle_index = end_pos
#         self._prepare_tick_buffer()
#         return result_candles

#     def get_tick(self, symbol: str) -> Optional[Tick]:
#         if self.tick_pointer_within_candle >= len(self.tick_buffer):
#             if self.current_candle_index + 1 >= len(self.candles_data):
#                 return None
#             self.current_candle_index += 1
#             self._prepare_tick_buffer()
#         tick = self.tick_buffer[self.tick_pointer_within_candle]
#         self.tick_pointer_within_candle += 1
#         return tick

#     def close_position(self, ticket, symbol):
#         return {
#             "done": True,
#             "ticket": 123456789,
#             "comment": "Done"
#         }

#     def place_bracket_order(self, symbol, vol, buy_sell, sl_price, tp_price, price):
#         return {
#             "done": True,
#             "ticket": 123456789,
#             "comment": "Done"
#         }

#     def account_details(self):
#         return {
#             "balance": 0,
#         }

# from datetime import datetime, timedelta
# from typing import List, Optional

# from typing import NamedTuple, Optional


# class Candle(NamedTuple):
#     time: int
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: float


# class Tick(NamedTuple):
#     time: int
#     bid: float
#     ask: float


# class Order(NamedTuple):
#     symbol: str
#     order_type: str
#     price: float
#     volume: float
#     stop_loss: Optional[float] = None
#     take_profit: Optional[float] = None
#     order_id: Optional[int] = None

# class MT5HistoricalProvider():
#     def __init__(self, ):
       

#     def _load_candle_data(self) -> List[Candle]:
#         rates = mt5.copy_rates_from(self.symbol, mt5.TIMEFRAME_M1, self.start_date, self.candle_count)
#         if rates is None:
#             raise RuntimeError(f"Failed to fetch candle data from MT5 for {self.symbol}")
#         return [Candle(rate['time'], rate['open'], rate['high'], rate['low'], rate['close'], rate['tick_volume']) for rate in rates]

#     def _load_tick_data(self, candle_time: int) -> List[Tick]:
#         ticks = mt5.copy_ticks_from(self.symbol, candle_time, self.tick_count, mt5.COPY_TICKS_ALL)
#         if ticks is None:
#             raise RuntimeError(f"Failed to fetch tick data from MT5 for {self.symbol}")
#         return [Tick(tick['time'], tick['bid'], tick['ask']) for tick in ticks]

#     def _prepare_tick_buffer(self):
#         current_candle_time = self.candles_data[self.current_candle_index].time
#         next_candle_time = current_candle_time + 60
#         self.tick_buffer = [tick for tick in self.ticks_data if current_candle_time <= tick.time < next_candle_time]
#         self.tick_pointer_within_candle = 0
#         if not self.tick_buffer:
#             self.ticks_data = self._load_tick_data(current_candle_time)
#             self.tick_buffer = [tick for tick in self.ticks_data if current_candle_time <= tick.time < next_candle_time]
#             self.tick_pointer_within_candle = 0

#     def get_candles(self, symbol: str, timeframe: str, start_pos: int, count: int) -> List[Candle]:
#         end_pos = self.current_candle_index + count
#         if end_pos > len(self.candles_data):
#             raise RuntimeError("Insufficient candle data for requested range.")
#         result_candles = self.candles_data[self.current_candle_index:end_pos]
#         self.current_candle_index = end_pos
#         self._prepare_tick_buffer()
#         return result_candles

#     def get_tick(self, symbol: str) -> Optional[Tick]:
#         if self.tick_pointer_within_candle >= len(self.tick_buffer):
#             if self.current_candle_index + 1 >= len(self.candles_data):
#                 return None
#             self.current_candle_index += 1
#             self._prepare_tick_buffer()
#         tick = self.tick_buffer[self.tick_pointer_within_candle]
#         self.tick_pointer_within_candle += 1
#         return tick

#     def place_order(self, order: Order) -> bool:
#         return True

#     def modify_order(self, order_id: int, new_order: Order) -> bool:
#         raise NotImplementedError

#     def cancel_order(self, order_id: int) -> bool:
#         raise NotImplementedError


# provider = MT5HistoricalProvider("EURUSD", datetime(2023, 1, 1))
# candles = provider.provider.get_candles("EURUSD", "M1", 0, 1)
# print(candles)