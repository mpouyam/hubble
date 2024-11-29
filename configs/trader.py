from typing import Optional, Dict, Tuple

from internal_types import OrderDirection
from .box import BoxConfig
from .order import OrderConfig


class TraderConfigCalculator:
    def __init__(self, config_dict: dict):
        self.symbol: str = config_dict["symbol"]
        self.point: float = config_dict["point"]
        self.sl_limit: float = config_dict["sl_limit"]
        self.tp_limit: float = config_dict["tp_limit"]
        self.static_vol: Optional[Dict[int, float]] = config_dict["static_vol"]
        self.static_tp: Optional[Dict[int, float]] = config_dict["static_tp"]
        self.static_sl: Optional[Dict[int, float]] = config_dict["static_sl"]
        self.growth_factor: float = config_dict["growth_factor"]

        self.pause_times: int = config_dict["pause_times"]
        self.max_order: int = config_dict["max_order"]

        self.directions_order: Dict[int , OrderDirection] | None = None
        self.signaller_name = ""

    def set_direction(self, direction: OrderDirection) -> OrderDirection:
        first = direction
        second = OrderDirection.SELL if direction == OrderDirection.BUY else OrderDirection.BUY
        self.directions_order = {
            1:first,
            2:second
        }

    def set_signaller_name(self, signaller_name: str) -> str:
        self.signaller_name = signaller_name
        return signaller_name

    def get_config(self) -> Tuple[BoxConfig, OrderConfig]:
        if self.directions_order is None:
            raise ValueError("Direction is not defined")

        box_recipes = BoxConfig(
            pause_times=self.pause_times,
            max_order=self.max_order
        )

        orders_recipes = OrderConfig(
            symbol=self.symbol,
            point=self.point,
            direction_order=self.directions_order,
            sl_limit=self.sl_limit,
            tp_limit=self.tp_limit,
            static_vol=self.static_vol,
            static_tp=self.static_tp,
            static_sl=self.static_sl,
            growth_factor=self.growth_factor,
            signaller_name=self.signaller_name
        )

        return box_recipes, orders_recipes

    def set_symbol(self, symbol) -> str:
        self.symbol = symbol
        return symbol

    def get_symbol(self) -> str:
        return self.symbol

    def get_signaller_name(self) -> str:
        return self.signaller_name
