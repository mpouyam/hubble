from typing import Tuple

import MetaTrader5 as mt5
import pytz
from datetime import datetime

from config import PlatformConfig


class Platform:
    instance: 'Platform'
    platform_config: PlatformConfig

    def __init__(self) -> None:
        pass

    def get_instance(self):
        if not hasattr(self, 'instance'):
            self.instance = Platform()

        return self.instance

    def initialize(self, platform_config: PlatformConfig):
        self.platform_config = platform_config
        if mt5.initialize(
                path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",  # platform_config.get_path(),
                login=platform_config.get_login(),
                password=platform_config.get_password(),
                server=platform_config.get_server(),
        ):
            print("Platform Initialized Successfully.")
            return self
        else:
            raise Exception("Platform Initialization Failed!")

    @staticmethod
    def get_symbol_info_tick(symbol: str):
        tick_info = mt5.symbol_info_tick(symbol)
        return tick_info.time, tick_info.bid, tick_info.ask, tick_info.volume

    @staticmethod
    def get_symbol_info(symbol: str) -> Tuple[str, str, float]:
        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            raise Exception("Symbol Not Found!")

        point = symbol_info.point * 10
        return symbol_info.currency_base, symbol_info.currency_profit, point

    @staticmethod
    def close_position(ticket, symbol):
        result = mt5.Close(symbol, ticket=ticket)

        if result:
            return {
                "done": True,
                "ticket": ticket,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "ticket": None,
                "comment": result.comment
            }

    @staticmethod
    def place_bracket_order(symbol, vol, buy_sell, sl_price, tp_price, price):

        direction = mt5.ORDER_TYPE_BUY if buy_sell.startswith("B") else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": direction,
            "sl": sl_price,
            "tp": tp_price,
            "price": price,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done": True,
                "ticket": result.order,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "ticket": None,
                "code": result.retcode,
                "comment": result.comment
            }

    @staticmethod
    def place_buy_order(symbol, vol, price, sl, tp):

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "sl": sl,
            "tp": tp,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        result = mt5.order_send(request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done": True,
                "ticket": result.order,
                "price": result.price,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "ticket": None,
                "code": result.retcode,
                "comment": result.comment
            }

    @staticmethod
    def place_sell_order(symbol, vol, price, sl, tp):

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "sl": sl,
            "tp": tp,
            "type": mt5.ORDER_TYPE_SELL,
            "price": price,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done": True,
                "ticket": result.order,
                "price": result.price,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "ticket": None,
                "code": result.retcode,
                "comment": result.comment
            }

    @staticmethod
    def modify_tp_sl_order(ticket, sl: float = None, tp: float = None):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
        }

        if sl is not None:
            request["sl"] = sl

        if tp is not None:
            request["tp"] = tp

        result = mt5.order_send(request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done": True,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "comment": result.comment,
                "code": result.retcode
            }

    @staticmethod
    def place_pend_order(symbol, vol, buy_sell, sl, tp, cp):
        direction = mt5.ORDER_TYPE_BUY_STOP if buy_sell.startswith("B") else mt5.ORDER_TYPE_SELL_STOP

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": vol,
            "price": cp,
            "sl": sl,
            "tp": tp,
            "type": direction,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done": True,
                "ticket": result.order,
                "comment": "Done"
            }
        else:
            return {
                "done": False,
                "ticket": None,
                "comment": result.comment
            }

    @staticmethod
    def account_details():
        account_det = mt5.account_info()
        return {
            "balance": account_det.balance,
            "equity": account_det.equity,
            "margin": account_det.margin,
            "free margin": account_det.margin_free
        }

    @staticmethod
    def historic_data(startDate, endDate, symbol: str):
        timezone = pytz.timezone("Etc/UTC")
        # create 'datetime' objects in UTC time zone to avoid the implementation of a local time zone offset
        utc_from = datetime(startDate[0], startDate[1], startDate[2], startDate[3], startDate[4], startDate[5],
                            tzinfo=timezone)
        utc_to = datetime(endDate[0], endDate[1], endDate[2], endDate[3], endDate[4], endDate[5], tzinfo=timezone)

        hist_data = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_INFO)
        return hist_data

    @staticmethod
    def get_recent_candles(
            symbol,
            timeframe,
            number_of_candles,
            start_position
    ):
        return mt5.copy_rates_from_pos(symbol, timeframe, start_position, number_of_candles)

