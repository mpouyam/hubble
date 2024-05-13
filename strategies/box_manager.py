import uuid
from enum import StrEnum
from typing import Any, Dict, Tuple
from datetime import datetime, time
import pytz

from publisher import TickListener
from trading_platform import Platform
from repository import BoxRepositoryInterface
from utils import now_time_iran , is_market_closed
from .order_manager import OrderManager , OrderStatus

class BoxErrorStatus(StrEnum):
    PLACE_ORDER_ERROR = "PLACE_ORDER_ERROR"
    STATE_MANAGER_ERROR = "STATE_MANAGER_ERROR"


class BoxSignal(StrEnum):
    ON = "ON"
    OFF = "OFF"
    OFFF = "OFFF"


class BoxState(StrEnum):
    INIT = "INIT"
    RUNNING =  "RUNNING"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"


class BoxManager(TickListener):

    # constructor
    def __init__(
        self, provider: type[Platform], logger: Any, repository: BoxRepositoryInterface
    ) -> None:
        self.provider = provider 
        self.box_repository = repository
        self.logger = logger
        self.signal = BoxSignal.ON # TODO: change this
        self.box = self.__initialize_box()
        self.default_working_hours = (9, 8) # Default: 9 AM to 8 PM
        self.working_hours = {
            # 0: (9, 17),  # Monday: 9 AM to 5 PM
            # 1: (9, 17),  # Tuesday: 9 AM to 5 PM
            # 2: (9, 14),  # Wednesday: 9 AM to 5 PM
            # 3: (9, 17),  # Thursday: 9 AM to 5 PM
            # 4: (9, 17),  # Friday: 9 AM to 5 PM
            # 5: (9, 17),  # Saturday: 9 AM to 5 PM
            # 6: (9, 17),  # Sunday: 9 AM to 5 PM
        }

        self.order_manager = OrderManager(provider , logger , self.box["symbol"])

    def __initialize_box(self) -> Dict[str, Any]:
        return {
            "id": uuid.uuid4(),
            "symbol" : "GBPUSD",
            "state": BoxState.INIT,
            "orders": [None],
            "active_index": 1,
            "started_at": now_time_iran(),
            "ended_at": None,
        }

    # public method
    def on_tick(self, tick: Tuple[int ,float, float]) -> None:
        self.__state_manager(bid=tick[1], ask=tick[2])

    def get_symbol(self) -> str:
        return self.box["symbol"]

    def handle_signal(self, signal: BoxSignal):

        if signal not in BoxSignal:
            self.logger.error(f"Invalid signal received: {signal}")
            return
        
        elif is_market_closed() or not self.is_working_hours():
            self.logger.warning("Received signal, but not within working hours.")
            return
        
        else:
            self.logger.info(f"Signal received: {signal}")
        
            if signal == BoxSignal.ON:
                if self.box["state"] != BoxState.RUNNING:
                    self.__reset_box_state()
                    self.signal = BoxSignal.ON
                else:
                    self.logger.warning("Received start signal but a box is already running.")
        
            elif signal == BoxSignal.OFF:
                if self.box["state"] == BoxState.RUNNING:
                    self.logger.warning("Received off signal. Waiting for the current box to finish.")
                    self.signal = BoxSignal.OFF                
                else:
                    self.logger.warning("Received off signal, but no box is running.")
            
            elif signal == BoxSignal.OFFF:
                self.logger.error("Received offf (off force) signal. Stopping the current box.")
                self.signal = BoxSignal.OFFF
                self.box["state"] = BoxState.STOPPED
                # TODO: close active order
                self.box_repository.save_box_data(self.box)
        


    # Manage state
    def __state_manager(self, bid: float, ask: float) -> None:
        box_state = self.box["state"]
        active_order_number = self.box["active_index"]

        if is_market_closed() :
            self.logger.warning("Market Is Close")
            return

        if self.signal == BoxSignal.OFFF:
            self.logger.warning("Box Is in OFFF Mode")
            return
        
        if self.signal == BoxSignal.OFF and box_state != BoxState.RUNNING:
            self.logger.warning("Box Is in OFF Mode")
            return
                
        if self.signal == BoxSignal.ON and not self.__is_working_hours() and box_state != BoxState.RUNNING:
            self.logger.warning("Box Is ON Mode but not within working hours")
            return
        
        
        if box_state == BoxState.INIT:
            order = self.order_manager.place_order(active_order_number)
            self.box["orders"].insert(active_order_number ,order)
            self.box["state"] = BoxState.RUNNING

        elif box_state == BoxState.RUNNING:
            order = self.order_manager.process_order(bid, ask)
                
            if order["status"] == OrderStatus.TP :
                self.box["orders"].insert(active_order_number , order)
                self.box["ended_at"] = now_time_iran()
                self.box["state"] = BoxState.FINISHED
                print("====================================")
                print(self.box["orders"])
                print("====================================")

                self.__save_box_data()
                self.__reset_box_state()


            elif order["status"] == OrderStatus.SL :
                self.box["orders"].insert(active_order_number , order)
                self.box["active_index"] += 1
                active_order = self.order_manager.place_order(self.box["active_index"])
                self.box["orders"].insert(self.box["active_index"] , active_order)
                return
                
            else:
                return
                    
        else: 
            if self.signal == BoxSignal.ON: 
                self.__reset_box_state()
                return
    
    def __reset_box_state(self):
        self.box = self.__initialize_box()

    def __save_box_data(self) -> None:
        self.box_repository.save_box_data(self.box)

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
