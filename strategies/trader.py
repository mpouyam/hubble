from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Tuple
from enum import StrEnum
from typing import Dict, Tuple, Union, TypedDict
import pytz
from dataclasses import dataclass

from repository import BoxRepositoryInterface
from trading_platform import Platform
from utils import is_market_closed
from .box_manager import BoxManager, BoxSignal, BoxConfig
from utils import format_gmt_time
from .order_manager import OrderDirection


class TraderSignal(StrEnum):
    ON = "ON"
    SHUT_DOWN = "SHUT_DOWN"


class Status(StrEnum):
    ON = "ON"
    OFF = "OFF"


@dataclass
class TraderConfig:
    default_working_hours: Tuple[float, float]
    working_hours: Dict[int, Tuple[float, float]]
    default_not_working_hours: Tuple[float, float]
    not_working_hours: Dict[int, Tuple[float, float]]


@dataclass
class OrdersConfig:
    symbol: str
    first_order_signal: str
    pip_unit: Union[None, float]
    try_count: int
    tp_limit: int
    sl_limit: int
    base_lot: float
    growth_factor: float
    static_vol: Dict[int, float]
    static_tp: Dict[int, int]
    static_sl: Dict[int, int]


@dataclass
class Config(TypedDict):
    trader_config: TraderConfig
    orders_config: OrdersConfig


@dataclass
class TraderSignalData(TypedDict):
    symbol: str
    direction: OrderDirection


class Trader(BoxManager):

    def __init__(self, provider, logger, repository: BoxRepositoryInterface, config=None) -> None:
        self.logger = logger
        self.repository = repository
        self.provider = provider

        self.status = Status.OFF
        self.clock = None
        self.config = None
        self.next_box_config = None
        self.__initialize_config(config)

    # public method
    def on_tick(self, tick: Tuple[int, float, float, float]) -> None:
        box_state = self._get_box_state()
        status = self.get_status()
        timestamp, bid, ask, vol = tick
        self.clock = int(timestamp)

        if is_market_closed(timestamp):
            self.logger.warning("Market Is Closed")
            return

        elif status == Status.OFF and box_state not in [BoxState.RUNNING, BoxState.PAUSE]:
            self.logger.warning("Box Is in OFF Mode")
            return

        elif status == Status.ON and box_state not in [BoxState.RUNNING,
                                                       BoxState.PAUSE] and not self.__is_working_hours():
            self.logger.warning("Box Is in ON Mode but not within working hours")
            return

        else:
            self._box_state_manager(bid, ask)
            return

    def get_symbol(self) -> str:
        return self.config["orders_config"]["symbol"]

    def handle_signal(self, signal: Signal):
        try:
            if signal not in Signal:
                self.logger.error(f"Invalid signal received: {signal}")
                return

            else:
                if signal == Signal.ON:
                    if self._get_box_state() not in [BoxState.RUNNING, BoxState.PAUSE]:
                        self.logger.warning("Received ON signal.")
                        self.__initialize_config(self.next_box_config)
                        self._reset_order_state()
                        self._reset_box_state()
                        self._set_status(Status.ON)
                        return

                elif signal == Signal.OFF:
                    self.logger.warning("Received OFF signal. Waiting for the current box to finish.")
                    self._set_status(Status.OFF)
                    return

                elif signal == Signal.OFFF:
                    self.logger.error("Received OFFF (OFF Force) signal. Stopping the current box")
                    self._set_status(Status.OFF)
                    self._set_box_state(BoxState.STOPPED)
                    self._close_order()
                    self._save_data()
                    return

                elif signal == Signal.PAUSE:
                    current_status = self.get_status()
                    if current_status == Status.ON:
                        self.logger.warning("Received PAUSE signal. Waiting for the current position to finish.")
                        self._handle_box_signal(BoxSignal.PAUSE)

                    return

                elif signal == Signal.RESUME:
                    current_status = self.get_status()
                    if current_status == Status.ON:
                        self.logger.warning("Received RESUME signal. Waiting for the current position to finish.")
                        self._handle_box_signal(BoxSignal.RESUME)

                    return

        except Exception as e:
            print("-----------------")
            print(e)
            print("-----------------")

    def get_status(self) -> Status:
        return self.status

    def change_config(self, config) -> None:
        data_dict = {key: value.__dict__ for key, value in config.items()}
        self.next_box_config = data_dict

    def get_all_status(self):
        box_status = self._get_box_state()
        return f'{self.status} : {box_status}'

    # private method
    def __is_working_hours(self) -> bool:
        # Define the GMT timezone
        gmt_tz = pytz.timezone('GMT')

        # Convert self.clock (which is a timestamp) to a datetime object in GMT timezone
        timestamp_time = datetime.fromtimestamp(self.clock, tz=gmt_tz)

        # Get the current day of the week (Monday=0, Sunday=6)
        current_day = timestamp_time.weekday()

        # Get working hours for the current day, or default if not specified
        working_hours = self.config["trader_config"]["working_hours"].get(
            current_day,
            self.config["trader_config"]["default_working_hours"]
        )

        # Parse start and end hours as floats
        start_hour, end_hour = working_hours

        # Extract hour and minute from start_hour and end_hour
        start_hour_int = int(start_hour)
        start_minute = int(round((start_hour - start_hour_int) * 100))
        end_hour_int = int(end_hour)
        end_minute = int(round((end_hour - end_hour_int) * 100))

        # Define start and end times for the current day's working hours
        start_time = datetime.combine(timestamp_time.date(), time(hour=start_hour_int, minute=start_minute))
        end_time = datetime.combine(timestamp_time.date(), time(hour=end_hour_int, minute=end_minute))

        # Localize start_time and end_time to GMT timezone
        start_time = gmt_tz.localize(start_time)
        end_time = gmt_tz.localize(end_time)

        # Check if the timestamp_time is within working hours
        return start_time <= timestamp_time <= end_time

    def _set_status(self, status: Status) -> None:
        self.status = status

    def _save_data(self) -> None:

        if self.state != BoxState.INIT and len(self.orders) > 0:
            account = self.provider.account_details()
            self.box["state"] = self.state
            self.box["ended_at"] = format_gmt_time(self.clock)
            self.box["orders"] = self._get_orders_list()
            self.box["profit"] = account["balance"] - self.box["profit"]
            self.repository.save_box_data(self.box)

    def __initialize_config(self, config=None) -> Config:

        if self.config is None and config is None:
            current_config = self.__default_configs()
        elif self.config is None and config is not None:
            current_config = config
        elif self.config is not None and config is None:
            current_config = self.config
        elif self.config is not None and config is not None:
            current_config = config

        # if self.config is not None:
        # #     # Update result with the provided config, but only for existing fields
        # #     # for section, values in config.items():
        # #     #     if section in current_config:
        # #     #         current_config[section].update({k: v for k, v in values.items() if k in current_config[section]})
        # #     for section, values in config.items():
        # #         if section in current_config:
        # #             current_config[section].update({k: v for k, v in values.items() if k in current_config[section]})

        #     # Update result with the provided config, but only for existing fields
        #     for section, values in self.config.items():
        #         if section in current_config:
        #             current_config[section].update({k: v for k, v in values.items() if k not in current_config[section]})
        #         else:
        #             current_config[section] = values

        if self.next_box_config is not None:
            self.next_box_config = None

        current_config["orders_config"]["pip_unit"] = self.provider.get_symbol_pip_unit(
            current_config["orders_config"]["symbol"])

        self.config = current_config

    def __default_configs(self) -> Config:
        return {
            "trader_config": {
                "default_working_hours": (7.00, 21.00),
                "working_hours": {},
                "default_not_working_hours": (13.00, 17.00),
                "not_working_hours": {},
            },
            "orders_config": {
                "symbol": "GBPUSD_o",
                "first_order_signal": "BUY",
                "pip_unit": None,
                "try_count": 9,
                "tp_limit": 6,
                "sl_limit": 1,
                "base_lot": 0.1,
                "growth_factor": 1.3,
                "static_vol": {
                    1: 0.01,
                    2: 0.01,
                    3: 0.01,
                    4: 0.02,
                    5: 0.02,
                    6: 0.03,
                    7: 0.04,
                    8: 0.05,
                    9: 0.06,
                    10: 0.08,
                    11: 0.1
                },
                "static_tp": {},
                "static_sl": {},
            }
        }


class TraderState(ABC):
    _trader_manager: 'TraderManager' = None

    @property
    def trader_manager(self) -> 'TraderManager':
        return self._trader_manager

    @trader_manager.setter
    def trader_manager(self, trader_manager: 'TraderManager') -> None:
        self._trader_manager = trader_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: TraderSignal, data) -> None:
        pass


class TraderManager:
    _state: TraderState = None

    def __init__(self, provider: Platform, logger, traderConfig: BoxConfig, timeManager) -> None:

        self.provider = provider
        self.logger = logger
        self.box_manager = None
        self.time_manager = timeManager
        self.transition_to(Listening())

    def transition_to(self, state: TraderState) -> None:
        self._state = state
        self._state.box_manager = self

    def on_signal(self, signal: BoxSignal, data) -> None:
        if signal not in BoxSignal:
            return
        else:
            self._state.on_signal(signal)

    def on_tick(self, tick) -> None:
        self._state.on_tick(tick)


class Listening(TraderState):
    clock: int

    def on_tick(self, tick) -> None:
        self.clock = tick[0]

    def on_signal(self, signal: TraderSignal, data: TraderSignalData) -> None:
        if signal == TraderSignal.SHUT_DOWN:
            return

        if self.trader_manager.box_manager is not None:
            self.trader_manager.transition_to(Processing())
            return

        if not self.__is_working_hour():
            return
        self.box_manager.order_manager.on_signal(OrderSignal.CLOSE)

    def __is_working_hour(self) -> bool:
        time = format_gmt_time(self.clock)
        return True


class Preparing(TraderState):

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: BoxSignal) -> None:
        if signal == BoxSignal.CLOSE:
            self.box_manager.transition_to(Finished())
        elif signal != BoxSignal.RESUME:
            self.box_manager.transition_to(Preparing())

    def on_tick(self, tick) -> None:
        return


class Processing(TraderState):
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

    def __tp_action(self):
        self.box_manager.ended_at = format_gmt_time(self.clock)
        self.box_manager.transition_to(Finished())

    def __sl_action(self):
        # check situation for pause
        if self.box_manager.active_order_number in self.box_manager.pause_times:
            self.box_manager.transition_to(Paused())
        else:
            self.box_manager.transition_to(Preparing())

    def __close_action(self):
        self.box_manager.ended_at = format_gmt_time(self.clock)
        self.box_manager.transition_to(Finished())

    def __error_action(self, error_code: OrderErrorStatus):
        if error_code == OrderErrorStatus.PLACING:
            self.box_manager.ended_at = format_gmt_time(self.clock)
            self.box_manager.transition_to(Finished())
        elif error_code == OrderErrorStatus.CLOSING:
            self.box_manager.ended_at = format_gmt_time(self.clock)
            self.box_manager.transition_to(Finished())


class Finished(TraderState):

    def on_signal(self, signal: BoxSignal) -> None:
        return

    def is_done(self) -> bool:
        return True

    def on_tick(self, tick) -> None:
        return
