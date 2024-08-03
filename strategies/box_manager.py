import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, TYPE_CHECKING, Optional, Tuple, List, Callable
from trading_platform import Platform
from utils import format_gmt_time
from .order_manager import OrderStatus, OrderDirection, OrderDetail, OrderManager, OrderInfo, OrderSignal, \
    OrderErrorStatus


class BoxErrorStatus(StrEnum):
    STATE_MANAGER_ERROR = "STATE_MANAGER_ERROR"


class BoxStatus(StrEnum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class BoxSignal(StrEnum):
    RESUME = "RESUME"
    CLOSE = "CLOSE"


if TYPE_CHECKING:
    from box_manager import BoxManager, OrderCalculator  # Import BoxManager only for type checking


@dataclass
class BoxConfig:
    pause_times: int
    max_order: int


class BoxState(ABC):
    _box_manager: 'BoxManager' = None

    @property
    def box_manager(self) -> 'BoxManager':
        return self._box_manager

    @box_manager.setter
    def box_manager(self, box_manager: 'BoxManager') -> None:
        self._box_manager = box_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: BoxSignal) -> None:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass


class BoxManager:
    _state: BoxState = None

    def __init__(self, provider: Platform, logger, boxConfig: BoxConfig, orderCalculator: OrderCalculator) -> None:

        self.provider = provider
        self.logger = logger
        self.order_manager = None
        self.order_calculator = orderCalculator
        self.box_config = boxConfig
        self.pause_times = self.__calculate_pause_times()

        account = self.provider.account_details()
        self.balance = account["balance"]

        self.id = uuid.uuid4()
        self.orders: list[OrderInfo] = []
        self.active_order_number = 0
        self.next_order_number = 1
        self.started_at = None
        self.ended_at = None

        self.transition_to(Preparing())

    def transition_to(self, state: BoxState) -> None:
        self._state = state
        self._state.box_manager = self

    def on_signal(self, signal: BoxSignal) -> None:
        if signal not in BoxSignal:
            return
        else:
            self._state.on_signal(signal)

    # Manage state
    def on_tick(self, tick) -> None:
        self._state.on_tick(tick)

    def __calculate_pause_times(self) -> List[int]:
        pause_times = self.box_config.pause_times
        max_order = self.box_config.max_order
        pause_numbers = []
        for n in range(max_order):
            if n % pause_times == 0 and n != 0:
                pause_numbers.append(n)

        return pause_numbers


class Preparing(BoxState):
    clock: int

    def on_tick(self, tick) -> None:
        self.clock = tick[0]

        if self.box_manager.order_manager is None:
            order_number = self.box_manager.next_order_number
            order_detail = self.box_manager.order_calculator.get_config(order_number)
            order_manager = OrderManager(self.box_manager.provider, self.box_manager.logger, order_detail)
            self.box_manager.order_manager = order_manager
            self.__moving_order_number()

        self.box_manager.transition_to(Processing())

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: BoxSignal):
        if signal == BoxSignal.CLOSE and self.box_manager.order_manager is not None:
            self.box_manager.order_manager.on_signal(OrderSignal.CLOSE)

    def __moving_order_number(self) -> None:
        self.box_manager.started_at = format_gmt_time(self.clock)
        self.box_manager.active_order_number = self.box_manager.next_order_number
        self.box_manager.next_order_number += 1


class Processing(BoxState):
    clock: int
    order_errors_need_action = [OrderErrorStatus.PLACING, OrderErrorStatus.CLOSING]

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: BoxSignal) -> None:
        if signal == BoxSignal.CLOSE and self.box_manager.order_manager is not None:
            self.box_manager.order_manager.on_signal(OrderSignal.CLOSE)

    def on_tick(self, tick) -> None:
        clock = tick[0]
        order_is_done = self.box_manager.order_manager.is_done()

        if order_is_done:
            order = self.box_manager.order_manager.get_prototype()
            self.box_manager.orders.append(order)
            self.box_manager.order_manager = None
            self.__handle_order(order)

        else:
            self.box_manager.order_manager.on_tick(tick)

    def __handle_order(self, order: OrderInfo) -> None:
        order_status = order.status
        if order.error_status in self.order_errors_need_action:
            self.__error_action(order.error_status)
        elif order_status == OrderStatus.TP:
            self.__tp_action()
        elif order_status == OrderStatus.SL:
            self.__sl_action()
        elif order_status == OrderStatus.CLOSED:
            self.__close_action()

    def __tp_action(self) -> None:
        self.box_manager.ended_at = format_gmt_time(self.clock)
        self.box_manager.transition_to(Finished())

    def __sl_action(self) -> None:
        # check situation for pause
        if self.box_manager.active_order_number in self.box_manager.pause_times:
            self.box_manager.transition_to(Paused())
        else:
            self.box_manager.transition_to(Preparing())

    def __close_action(self) -> None:
        self.box_manager.ended_at = format_gmt_time(self.clock)
        self.box_manager.transition_to(Finished())

    def __error_action(self, error_code: OrderErrorStatus) -> None:
        if error_code == OrderErrorStatus.PLACING:
            self.box_manager.ended_at = format_gmt_time(self.clock)
            self.box_manager.transition_to(Finished())
        elif error_code == OrderErrorStatus.CLOSING:
            self.box_manager.ended_at = format_gmt_time(self.clock)
            self.box_manager.transition_to(Finished())


class Paused(BoxState):

    def on_signal(self, signal: BoxSignal) -> None:
        if signal == BoxSignal.CLOSE:
            self.box_manager.transition_to(Finished())
        elif signal != BoxSignal.RESUME:
            self.box_manager.transition_to(Preparing())

    def on_tick(self, tick) -> None:
        return

    def is_done(self) -> bool:
        return False


class Finished(BoxState):
    finished = False

    def on_signal(self, signal: BoxSignal) -> None:
        return

    def is_done(self) -> bool:
        return False

    def on_tick(self, tick) -> None:
        return


@dataclass
class OrderConfig:
    symbol: str
    point: float
    first_direction: OrderDirection
    sl_limit: float
    tp_limit: float
    static_vol: Optional[Dict[int, float]]
    static_tp: Optional[Dict[int, float]]
    static_sl: Optional[Dict[int, float]]
    growth_factor: float


class OrderCalculator:

    def __init__(self, orderConfig: OrderConfig) -> None:

        self.symbol = orderConfig.symbol
        self.point = orderConfig.point
        self.first_direction = orderConfig.first_direction
        self.sl_limit = orderConfig.sl_limit
        self.tp_limit = orderConfig.tp_limit
        self.static_vol = orderConfig.static_vol
        self.static_tp = orderConfig.static_tp
        self.static_sl = orderConfig.static_sl
        self.growth_factor = orderConfig.growth_factor

    def set_first_direction(self, direction: OrderDirection) -> None:
        self.first_direction = direction

    def get_config(self, orderNumber: int) -> OrderDetail:
        direction = self.__calculate_direction(orderNumber)
        volume = self.__calculate_vol(orderNumber)
        sl, tp = self.__calculate_sl_tp(orderNumber)

        return OrderDetail(
            symbol=self.symbol,
            unit=self.point,
            direction=direction,
            volume=volume,
            sl=sl,
            tp=tp
        )

    def __calculate_direction(self, orderNumber: int) -> OrderDirection:
        direction = self.first_direction

        if direction == OrderDirection.BUY:
            return OrderDirection.BUY if orderNumber % 2 != 0 else OrderDirection.SELL
        else:
            return OrderDirection.SELL if orderNumber % 2 == 0 else OrderDirection.BUY

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
