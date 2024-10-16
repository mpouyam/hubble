from config import PlatformConfig
from trading_platform import Platform


class PlatformMock(Platform):
    def __init__(self, platform_config: PlatformConfig) -> None:
        super().initialize(platform_config)

    def close_position(self, ticket, symbol):
        return {
            "done": True,
            "ticket": 123456789,
            "comment": "Done"
        }

    def place_bracket_order(self, symbol, vol, buy_sell, sl_price, tp_price, price):
        return {
            "done": True,
            "ticket": 123456789,
            "comment": "Done"
        }

    def account_details(self):
        return {
            "balance": 0,
        }
