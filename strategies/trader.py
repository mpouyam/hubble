from datetime import datetime, time
from typing import Tuple
from enum import StrEnum
import pytz


from repository import BoxRepositoryInterface
from utils import is_market_closed
from .box_manager import BoxManager , BoxState
from utils import now_time_iran

class Signal(StrEnum):
    ON = "ON"
    OFF = "OFF"
    OFFF = "OFFF"
    CONFIG = "CONFIG"

class Status(StrEnum):
    ON = "ON"
    OFF = "OFF"

class Trader(BoxManager):
    def __init__(self , provider , logger , repository:BoxRepositoryInterface , symbol:str) -> None:

        self.logger = logger
        self.repository = repository
        self.provider = provider
        self.symbol = symbol
        self.status = Status.OFF
        self.default_working_hours = (9, 21)
        self.working_hours = {
            # 0: (9, 17),  # Monday: 9 AM to 5 PM
            # 1: (9, 17),  # Tuesday: 9 AM to 5 PM
            # 2: (9, 14),  # Wednesday: 9 AM to 5 PM
            # 3: (9, 17),  # Thursday: 9 AM to 5 PM
            # 4: (9, 17),  # Friday: 9 AM to 5 PM
            # 5: (9, 17),  # Saturday: 9 AM to 5 PM
            # 6: (9, 17),  # Sunday: 9 AM to 5 PM
        }
        super().__init__()

    # public method
    def on_tick(self, tick:Tuple[int , float , float , float]) -> None:
        box_state = self._get_box_state()
        status = self.get_status()

        if is_market_closed() :
            self.logger.warning("Market Is Closed")
            return
        
        elif status == Status.OFF and box_state != BoxState.RUNNING:
            self.logger.warning("Box Is in OFF Mode")
            return
                
        elif status == Status.ON and box_state != BoxState.RUNNING and not self.__is_working_hours() :
            self.logger.warning("Box Is ON Mode but not within working hours")
            return
        
        else:
            self._box_state_manager(bid=tick[1], ask=tick[2])
            return

    def get_symbol(self) -> str:
        return self.symbol

    def handle_signal(self, signal: Signal):
        if signal not in Signal:
            self.logger.error(f"Invalid signal received: {signal}")
            return
        
        else:
            if signal == Signal.ON:
                self.logger.warning("Received ON signal.")
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

            elif signal == Signal.CONFIG:
                print("config changed , next box should open with new config")
    
    def get_status(self) -> Status:
        return self.status


    # private method
    def __is_working_hours(self) -> bool:

        ir_timezone = pytz.timezone('Asia/Tehran')  # Use Tehran timezone for Iran
        # Get the current time in Iranian timezone
        current_time = datetime.now(ir_timezone)

        # Get current day of the week (Monday=0, Sunday=6)
        current_day = current_time.weekday()

        # Get working hours for the current day, or default if not specified
        working_hours = self.working_hours.get(current_day, self.default_working_hours)

        # Define start and end times for the current day's working hours
        start_time = time(working_hours[0], 0)
        end_time = time(working_hours[1], 0)

        # Check if the current time is within working hours
        return start_time <= current_time.time() <= end_time

    def _set_status(self , status : Status) -> None :
        self.status = status
    
    def _save_data(self) -> None:
        if self.state != BoxState.INIT:
            self.box["state"] = self.state
            self.box["ended_at"] = now_time_iran()
            self.box["orders"] = self._get_orders_list()
            self.repository.save_box_data(self.box)
