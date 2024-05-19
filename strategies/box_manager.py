import uuid
from enum import StrEnum
from typing import Any, Dict

from utils import now_time_iran
from .order_manager import OrderManager , OrderStatus, OrderState

class BoxErrorStatus(StrEnum):
    STATE_MANAGER_ERROR = "STATE_MANAGER_ERROR"


class BoxState(StrEnum):
    INIT = "INIT"
    RUNNING =  "RUNNING"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"

class BoxManager(OrderManager):

    # constructor
    def __init__(self) -> None:
        self.state = BoxState.INIT
        self.box = self.__initialize_box()
        super().__init__()

    def __initialize_box(self) -> Dict[str, Any]:
        account = self.provider.account_details()
        return {
            "id": uuid.uuid4(),
            "symbol" : self.symbol,
            "orders": None,
            "active_index": 1,
            "started_at": now_time_iran(),
            "profit": account["balance"],
            "ended_at": None,
        }


    # Manage state
    def _box_state_manager(self, bid: float, ask: float) -> None:
        box_state = self._get_box_state()
        active_order_number = self.box["active_index"]
        try:

            if box_state == BoxState.INIT:
                self._init_action(active_order_number , bid , ask)

            elif box_state == BoxState.RUNNING:
                order = self._process_order(bid, ask)
                order_status = order["status"]

                if order_status == OrderStatus.TP :
                    self._tp_action()

                elif order_status == OrderStatus.SL:
                    self._sl_action(bid,ask)
                    
                elif order_status == OrderStatus.NOTHING:
                    return

        except Exception:
            self._set_status("OFF")
            self._set_box_state(BoxState.STOPPED)
            self._save_data()

    def _init_action(self , active_order_number:int , bid: float, ask: float):

        active_order = self._place_order(active_order_number , bid, ask)

        if active_order["state"] != OrderState.ACTIVE: 
            raise Exception({
                "code": BoxErrorStatus.STATE_MANAGER_ERROR,
                "message": active_order["error"]
            })
        self._set_box_state(BoxState.RUNNING)

    def _tp_action(self):
        self._set_status("OFF")
        self._set_box_state(BoxState.FINISHED)
        self._save_data()

    def _sl_action(self , bid:float , ask:float):
        new_active_order_number = self.__overplus_box_active_order_number()
        new_active_order = self._place_order(new_active_order_number , bid , ask)

        if new_active_order["state"] != OrderState.ACTIVE: 
            raise Exception({
                "code": BoxErrorStatus.STATE_MANAGER_ERROR,
                "message": new_active_order["error"]
            })

    def _reset_box_state(self):
        self._set_box_state(BoxState.INIT)
        self.box = self.__initialize_box()

    def _set_box_state(self , state: BoxState) -> None:
        self.state = state
    
    def _get_box_state(self) -> BoxState:
        return self.state

    def __overplus_box_active_order_number(self) -> int:
        self.box["active_index"] += 1
        return self.box["active_index"]
