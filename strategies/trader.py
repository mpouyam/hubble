from datetime import datetime, time
from typing import Tuple
from enum import StrEnum
from typing import Dict, Tuple , Union,TypedDict
import pytz
from dataclasses import dataclass


from repository import BoxRepositoryInterface
from utils import is_market_closed
from .box_manager import BoxManager , BoxState , BoxSignal
from utils import now_time_iran

class Signal(StrEnum):
    ON = "ON"
    OFF = "OFF"
    OFFF = "OFFF"
    PAUSE = "PAUSE"
    RESUME = "RESUME"


class Status(StrEnum):
    ON = "ON"
    OFF = "OFF"

@dataclass
class TraderConfig:
    default_working_hours: Tuple[int, int]
    working_hours: Dict[int, Tuple[int, int]]
    default_not_working_hours: Tuple[int, int]
    not_working_hours: Dict[int, Tuple[int, int]]

@dataclass
class OrdersConfig:
    symbol: str
    first_order_signal: str
    pip_unit: Union[None, float]  # Change 'Any' to the appropriate type if available
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

class Trader(BoxManager):
    def __init__(self , provider , logger , repository:BoxRepositoryInterface , config = None) -> None:
        self.logger = logger
        self.repository = repository
        self.provider = provider
        
        self.status = Status.OFF
        self.clock = None
        self.config = None
        self.next_box_config = None
        self.__initialize_config(config)    
        super().__init__()

    # public method
    def on_tick(self, tick:Tuple[int , float , float , float]) -> None:
        box_state = self._get_box_state()
        status = self.get_status()
        timestamp , bid , ask , vol = tick 
        self.clock = int(timestamp)

        if is_market_closed(timestamp) :
            self.logger.warning("Market Is Closed")
            return
        
        elif status == Status.OFF and box_state not in [BoxState.RUNNING , BoxState.PAUSE] :
            self.logger.warning("Box Is in OFF Mode")
            return
                
        elif status == Status.ON and box_state not in [BoxState.RUNNING , BoxState.PAUSE] and not self.__is_working_hours() :
            self.logger.warning("Box Is in ON Mode but not within working hours")
            return
        
        else:
            self._box_state_manager(bid , ask)
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
                    if self._get_box_state() not in [BoxState.RUNNING , BoxState.PAUSE]:
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
                    if current_status == Status.ON and self._get_box_state == BoxState.PAUSE:
                        self.logger.warning("Received RESUME signal. Waiting for the current position to finish.")
                        self._handle_box_signal(BoxSignal.RESUME)

                    return
        
        except Exception as e :
            print("-----------------")
            print(e)
            print("-----------------")

    def get_status(self) -> Status:
        return self.status
    
    def change_config(self , config) -> None:
        data_dict = {key: value.__dict__ for key, value in config.items()}
        self.next_box_config = data_dict



    
    def get_all_status(self):
        box_status = self._get_box_state()
        return f'{self.status} : {box_status}'


    # private method
    def __is_working_hours(self) -> bool:
        # ir_timezone = pytz.timezone('Asia/Tehran')  # Use Tehran timezone for Iran
        
        # Convert timestamp to datetime in Iranian timezone if provided
        timestamp_time = datetime.fromtimestamp(self.clock, pytz.utc).time() #.astimezone(ir_timezone).time()
        
        # Get current day of the week (Monday=0, Sunday=6)
        current_day = datetime.now().weekday()

        # Get working hours for the current day, or default if not specified
        working_hours = self.config["trader_config"]["working_hours"].get(current_day, self.config["trader_config"]["default_working_hours"])

        # Define start and end times for the current day's working hours
        start_time = time(working_hours[0], 0)
        end_time = time(working_hours[1], 0)

        # Check if the current time is within working hours
        return start_time <= timestamp_time <= end_time

    def _set_status(self , status : Status) -> None :
        self.status = status
    
    def _save_data(self) -> None:

        if self.state != BoxState.INIT and len(self.orders) > 0: 
            account = self.provider.account_details()
            self.box["state"] = self.state
            self.box["ended_at"] = now_time_iran(self.clock)
            self.box["orders"] = self._get_orders_list()
            self.box["profit"] = account["balance"] - self.box["profit"] 
            self.repository.save_box_data(self.box)

    def __initialize_config(self  , config = None) -> Config:

        if self.config is None and config is None:
            current_config = self.__default_configs()
        elif self.config is None and config is not None:
            current_config = config
        elif self.config is not None and config is None :
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
        

        current_config["orders_config"]["pip_unit"]= self.provider.get_symbol_pip_unit(current_config["orders_config"]["symbol"])

        self.config = current_config

    
    def __default_configs(self) -> Config :
        return  {
            "trader_config": {
                "default_working_hours": (9, 21),
                "working_hours": {},
                "default_not_working_hours": (13, 17),
                "not_working_hours": {},
            },
            "orders_config": {
                "symbol": "GBPUSD_o",
                "first_order_signal": "BUY",
                "pip_unit": None,
                "try_count": 9,
                "tp_limit": 10,
                "sl_limit": 2,
                "base_lot": 0.1,
                "growth_factor": 1.3,
                "static_vol": {},
                "static_tp": {},
                "static_sl": {},
            }
        }
