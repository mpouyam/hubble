import uuid
from typing import List
from config import BoxConfig, OrderConfigCalculator
from .order import OrderManager
from platform import Platform
from type import  BoxSignal, BoxSignalData, Order, OrderSignal, OrderErrorStatus, OrderStatus
from utils import format_gmt_time
from abc import ABC, abstractmethod


class BoxManager:
    _state: 'BoxState' = None

    def __init__(self, provider: Platform, logger, config: BoxConfig, orderCalculator: OrderConfigCalculator) -> None:

        self.provider = provider
        self.logger = logger
        self.order_manager = None
        self.order_calculator = orderCalculator
        self.config = config
        self.pause_times = self.__calculate_pause_times()

        account = self.provider.account_details()
        self.balance = account["balance"]

        self.id = uuid.uuid4()
        self.orders: list[Order] = []
        self.active_order_number = 0
        self.next_order_number = 1
        self.started_at = None
        self.ended_at = None

        self.transition_to(Preparing())

    def transition_to(self, state: 'BoxState') -> None:
        self._state = state
        self._state.box_manager = self

    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        if signal not in BoxSignal:
            return
        else:
            self._state.on_signal(signal, data)

    # Manage state
    def on_tick(self, tick) -> None:
        self._state.on_tick(tick)

    def get_data(self):
        return {
            "id": str(self.id),
            "last_order": self.active_order_number,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "orders": self.orders,
            "config": self.config,
        }

    def __calculate_pause_times(self) -> List[int]:
        pause_times = self.config.pause_times
        max_order = self.config.max_order
        pause_numbers = []
        for n in range(max_order):
            if n % pause_times == 0 and n != 0:
                pause_numbers.append(n)

        return pause_numbers

class BoxState(ABC):
    _box_manager: BoxManager

    @property
    def box_manager(self) -> BoxManager:
        return self._box_manager

    @box_manager.setter
    def box_manager(self, box_manager: BoxManager) -> None:
        self._box_manager = box_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass

class Preparing(BoxState):

    def on_tick(self, tick) -> None:

        if self.box_manager.order_manager is None:
            self.box_manager.started_at = format_gmt_time(tick[0])

            active_order_number = self.box_manager.next_order_number
            order_recipes = self.box_manager.order_calculator.get_config(active_order_number)
            order_manager = OrderManager(self.box_manager.provider, self.box_manager.logger, order_recipes)

            self.box_manager.order_manager = order_manager

            self.__moving_order_number()

        self.box_manager.transition_to(Processing())

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        if signal == BoxSignal.CLOSE and self.box_manager.order_manager is not None:
            self.box_manager.order_manager.on_signal(OrderSignal.CLOSE)

    def __moving_order_number(self) -> None:
        self.box_manager.active_order_number = self.box_manager.next_order_number
        self.box_manager.next_order_number += 1


class Processing(BoxState):
    clock: int
    order_errors_need_action = [OrderErrorStatus.PLACING, OrderErrorStatus.CLOSING]

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        if signal == BoxSignal.CLOSE and self.box_manager.order_manager is not None:
            self.box_manager.order_manager.on_signal(OrderSignal.CLOSE)

    def on_tick(self, tick) -> None:
        order_is_done = self.box_manager.order_manager.is_done()

        if order_is_done:
            order = self.box_manager.order_manager.get_prototype()
            self.box_manager.orders.append(order)
            self.box_manager.order_manager = None
            self.__handle_order(order)

        else:
            self.box_manager.order_manager.on_tick(tick)

    def __handle_order(self, order: Order) -> None:
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
        self.box_manager.transition_to(Finished())

    def __sl_action(self) -> None:
        # check situation for pause
        if self.box_manager.active_order_number in self.box_manager.pause_times:
            self.box_manager.transition_to(Paused())
        else:
            self.box_manager.transition_to(Preparing())

    def __close_action(self) -> None:
        self.box_manager.transition_to(Finished())

    def __error_action(self, error_code: OrderErrorStatus) -> None:
        if error_code == OrderErrorStatus.PLACING:
            self.box_manager.transition_to(Finished())
        elif error_code == OrderErrorStatus.CLOSING:
            self.box_manager.transition_to(Finished())


class Paused(BoxState):

    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        if signal == BoxSignal.CLOSE:
            self.box_manager.transition_to(Finished())
        elif signal != BoxSignal.RESUME:
            self.box_manager.order_calculator.set_first_direction(data.get("direction"))
            self.box_manager.transition_to(Preparing())

    def on_tick(self, tick) -> None:
        return

    def is_done(self) -> bool:
        return False


class Finished(BoxState):
    finished = False

    def on_signal(self, signal: BoxSignal, data: BoxSignalData) -> None:
        return

    def is_done(self) -> bool:
        return self.finished

    def on_tick(self, tick) -> None:
        if not self.finished:
            self.box_manager.ended_at = format_gmt_time(tick[0])
            account = self.box_manager.provider.account_details()
            self.box_manager.balance = account["balance"] - self.box_manager.balance
            self.finished = True
        return
