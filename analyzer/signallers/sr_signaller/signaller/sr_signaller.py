import threading
import time
from datetime import datetime

import pandas as pd
from typing import Self, Tuple, List

from analyzer.signallers.sr_signaller.handler.sr_signal_handler import SRSignalHandler
from analyzer.signallers.sr_signaller.signal import SRSignal
from analyzer.signallers.sr_signaller.signal.sr_signal import SRSignalType
from fincore.signal_handler import SignalHandler
from fincore.signaller import Signaller, SignallerStatus
from trading_platform import Platform


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

    def get_inner_margin(self) -> float:
        return self.inner_margin

    def get_outer_margin(self) -> float:
        return self.outer_margin

    def get_min_touches(self) -> int:
        return self.min_touches

    def get_candle_frame(self) -> int:
        return self.candle_frame

    def get_candle_count(self) -> int:
        return self.candle_count


class SRSignaller(Signaller):

    def subscribe_handler(self, handler: SignalHandler) -> Self:
        self.handlers.append(handler)
        return self

    def unsubscribe_handler(self, handler: SignalHandler) -> Self:
        self.handlers.remove(handler)
        return self

    def stop(self):
        self.set_status(SignallerStatus.STOPPED)

    def is_ready(self) -> bool:
        with self.ready_lock:
            return self.ready

    def process(self):
        last_candle = 0
        while self.get_status() == SignallerStatus.RUNNING:
            candles = self.platform.get_recent_candles(
                self.config.symbol,
                self.config.candle_frame,
                self.config.candle_count + 1,
                1
            )
            candles = candles[['open', 'high', 'low', 'close']]
            if hash(last_candle) != hash(candles[-1]):
                print("Last Candle:", last_candle)
                print("New Candle:", candles[-1])
                last_candle = candles[-1]
                sr_signal = self.check_sr(candles)
                if sr_signal:
                    print(sr_signal)
                    for handler in self.handlers:
                        handler.handle_signal(sr_signal)
            time.sleep(5)


    def check_sr(self, candles: List[Tuple]) -> SRSignal | None:
        candles = pd.DataFrame(candles)
        print(candles)
        last_candle = candles.iloc[-1]
        candles = candles[:-1]

        support = candles['low'].min()
        resistance = candles['high'].max()
        supp_touches = len(candles[candles['low'] < support + self.config.inner_margin])
        res_touches = len(candles[candles['high'] > resistance - self.config.inner_margin])
        enough_touches = (supp_touches + res_touches) >= self.config.min_touches

        # print("Supp Touches:", supp_touches)
        # print("Res Touches:", res_touches)
        # print("Is Enough:", enough_touches)
        if not enough_touches:
            return None
        break_sup = last_candle['close'] < (support - self.config.outer_margin)
        break_res = last_candle['close'] > (resistance + self.config.outer_margin)

        # print("Break Sup:", break_sup)
        # print("Break Res:", break_res)

        if break_sup or break_res:
            sr_signal = (
                SRSignal(
                    datetime.now(),
                    SRSignalType.SUPPORT_BREAK if break_sup else SRSignalType.RESISTANCE_BREAK
                )
                    .set_min_touches(self.config.min_touches)
                    .set_actual_touches(supp_touches + res_touches)
                    .set_close_price(last_candle['close'])
                    .set_support_price(support)
                    .set_resistance_price(resistance)
            )
            return sr_signal
        return None

    def __init__(self, config: SRSignallerConfig, platform: Platform):
        super().__init__()
        self.config = config
        self.platform = platform
        self.handlers : List[SignalHandler] = []
        self.set_ready(True)

    def get_signaller_name(self) -> str:
        return 'SR Signaller'
