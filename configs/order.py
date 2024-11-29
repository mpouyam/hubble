from dataclasses import dataclass
from typing import Optional, Dict, Tuple

from internal_types import OrderDirection, OrderRecipes


@dataclass
class OrderConfig:
    symbol: str
    point: float
    direction_order: Dict[int , OrderDirection]
    sl_limit: float
    tp_limit: float
    static_vol: Optional[Dict[int, float]]
    static_tp: Optional[Dict[int, float]]
    static_sl: Optional[Dict[int, float]]
    growth_factor: float
    signaller_name: str


class OrderConfigCalculator:

    def __init__(self, orderConfig: OrderConfig) -> None:
        self.symbol = orderConfig.symbol
        self.point = orderConfig.point
        self.directions_order = orderConfig.direction_order
        self.sl_limit = orderConfig.sl_limit
        self.tp_limit = orderConfig.tp_limit
        self.static_vol = orderConfig.static_vol
        self.static_tp = orderConfig.static_tp
        self.static_sl = orderConfig.static_sl
        self.growth_factor = orderConfig.growth_factor
        self.signaller_name = orderConfig.signaller_name

    def get_config(self, orderNumber: int, direction:OrderDirection = None) -> OrderRecipes:
        direction = self.__calculate_direction(orderNumber , direction)
        volume = self.__calculate_vol(orderNumber)
        tp, sl = self.__calculate_sl_tp(orderNumber)

        return OrderRecipes(
            symbol=self.symbol,
            unit=self.point,
            direction=direction,
            volume=volume,
            sl=sl,
            tp=tp,
            signaller_name=self.signaller_name
        )

    def __calculate_direction(self, orderNumber: int , direction:OrderDirection = None) -> OrderDirection:
        which_direction = 1 if orderNumber % 2 != 0 else 2
        detected_direction = self.directions_order[which_direction]

        if not direction:
            return detected_direction
        elif direction == detected_direction:
            return detected_direction
        else:
            first = self.directions_order[1]
            self.directions_order[1] =  self.directions_order[2]   
            self.directions_order[2] = first
            return direction


    def __calculate_vol(self, orderNumber: int) -> float:
        if self.static_vol and orderNumber in self.static_vol:
            return self.static_vol[orderNumber]

        else:
            if self.static_vol:
                max_key = max(self.static_vol.keys())
                n = max_key
                b = self.static_vol[n]
            else:
                n = 0
                b = 0.1

            g = self.growth_factor
            p = orderNumber - n
            v = round((pow(g, p) * b), 2)

            return v

    def __calculate_sl_tp(self, orderNumber: int) -> Tuple[float, float]:
        sl = self.sl_limit
        tp = self.tp_limit

        if self.static_sl and orderNumber in self.static_sl:
            sl = self.static_sl[orderNumber]

        if self.static_tp and orderNumber in self.static_tp:
            tp = self.static_tp[orderNumber]

        return tp, sl
