from enum import StrEnum
import time
from typing import Tuple , Optional , TypedDict
from utils import format_gmt_time
from __future__ import annotations
from abc import ABC, abstractmethod

class OrderStatus(StrEnum):
    SL = "SL"
    TP = "TP"
    NOTHING = "NOTHING"

class OrderStates(StrEnum):
    INIT = "INIT"
    ACTIVE = "ACTIVE"
    DONE =  "DONE"
    CLOSED = "CLOSED"
    FAILED = "FAILED"

class OrderDirection(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

class OrderDetails(TypedDict):
    index: int
    buy_or_sell: str
    ticket: Optional[str]
    symbol: str
    volume: float
    sl: float
    tp: float
    price: float
    spread: float
    state: OrderState
    status: OrderStatus
    started_at: str
    ended_at: str
    error: Optional[str]

class SymbolInfo(TypedDict):
    name: str
    unit:float


class OrderManager():

    _state = None

    def __init__(self , direction:OrderDirection , symbol_info: SymbolInfo , volume:float , price:float , created_at: int, sl: float , tp:float):
        self.pip_unit = symbol_info["unit"]
        self.sl = sl
        self.tp = tp

        self.symbol = symbol_info["name"]
        self.direction = direction
        self.ticket = None
        self.volume = volume
        self.price = price
        self.status = OrderStatus.NOTHING
        self.created_at = created_at
        self.started_at = None
        self.ended_at = None
        self.error = None
        
        self.transition_to(InitState())

    def transition_to(self, state: OrderState):
        self._state = state
        self._state.order_manager = self
        self.state = state.get_status()

    def on_tick(self , tick):
        self._state.on_tick(tick)
    
    def _close_order(self) -> None:
        if self.state is not OrderState.ACTIVE:
            return

        active_order_ticket = self.ticket


        for attempt in range(9):

            result = self.provider.close_position(active_order_ticket , self.symbol)
            
            if result["done"]:
                self.state = OrderState.CLOSED
                self.ended_at = format_gmt_time(self.clock)
                return self

            else:
                self.logger.error(f"Attempt {attempt+1}: Failed To Close Active Order: {result['comment']}")
                self.logger.debug("Trying One More Time")
                time.sleep(0.3)
                
        self.logger.error("Maximum Retries Reached For Closing Active Order.")
        self.state = OrderState.FAILED
        self.error = result["comment"]
        
        return self
     
    # Process Orders
    def _process_order(self, bid: float, ask: float) -> OrderDetails:
        order_status = self.__process_buy_order(bid) if self.active_order["buy_or_sell"] == "BUY" else self.__process_sell_order(ask)

        if order_status != OrderStatus.NOTHING: 
            self.active_order["state"] = OrderState.DONE
            self.active_order["status"] = order_status
            self.active_order["ended_at"] = format_gmt_time(self.clock)
            self.__add_to_orders(self.active_order)
        
        return self.active_order

    def __process_buy_order(self, bid: float) -> OrderStatus:

        if bid >= self.active_order["tp"]:
            self.logger.critical("TP Touched For Buy Position...")
            return OrderStatus.TP

        elif bid <= self.active_order["sl"]:
            self.logger.warning("SL Touched For Buy Position...")
            return OrderStatus.SL
        
        else:
            return OrderStatus.NOTHING

    def __process_sell_order(self, ask: float) -> OrderStatus:
        if ask <= self.active_order["tp"]:
            self.logger.critical("TP Touched For Sell Position...")
            return OrderStatus.TP

        elif ask >= self.active_order["sl"]:
            self.logger.warning("SL Touched For Sell Position...")
            return OrderStatus.SL
        
        else:
            return OrderStatus.NOTHING

    #  Calculate Orders    
    def __calculate_order(self , order_number , bid=None , ask=None) -> None:
        buy_or_sell = self.__calculate_buy_or_sell(order_number)
        current_price = self.__calculate_current_price(buy_or_sell , bid , ask)
        volume = self.__calculate_vol(order_number)
        take_profit , stop_loss  = self.__calculate_tp_sl(current_price, buy_or_sell , order_number)


        self.active_order = {
            "index": order_number,
            "buy_or_sell": buy_or_sell,
            "ticket": None,
            "symbol": self.config["orders_config"]["symbol"],
            "volume": volume,
            "sl": stop_loss,
            "tp": take_profit,
            "price": current_price,
            "state": OrderState.INIT,
            "status": OrderStatus.NOTHING,
            "spread": None,
            "started_at": format_gmt_time(self.clock),
            "ended_at": None,
            "error": None
        }

        self.logger.info("Order Calculated !")

    def __calculate_buy_or_sell(self, index: int) -> str:
        signal = self.config["orders_config"]["first_order_signal"]
        start_with_buy = signal == "BUY"

        if start_with_buy:
            return "BUY" if index % 2 != 0 else "SELL"
        else:
            return "SELL" if index % 2 == 0 else "BUY"

    def __calculate_vol(self, index: int) -> float:
        v = None

        if index in self.config["orders_config"]["static_vol"]:
            v = self.config["orders_config"]["static_vol"][index]

        else:
            n = list(self.config["orders_config"]["static_vol"].keys())[-1] if self.config["orders_config"]["static_vol"] else 0
            g = self.config["orders_config"]["growth_factor"]
            p = index - n
            b = self.config["orders_config"]["base_lot"]
            v = round((pow(g, p) * b),2)

        return v
    
    def __calculate_tp_sl(self) -> Tuple[float, float]:

        tp_limit = self.config["orders_config"]["tp_limit"]
        sl_limit = self.config["orders_config"]["sl_limit"]
        pip_unit = self.config["orders_config"]["pip_unit"]

        tp_pip = pip_unit * tp_limit
        sl_pip = pip_unit * sl_limit
        cp = self.price

        if self.direction == OrderDirection.SELL:
            tp_price = cp - tp_pip
            sl_price = cp + sl_pip

        elif self.direction == OrderDirection.BUY:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        final_tp_price = round(tp_price, 5)
        final_sl_price = round(sl_price, 5)

        return (final_tp_price, final_sl_price)

    def __calculate_current_price(self, buy_or_sell: str , bid = None , ask = None ) -> float:
        price = 0.0
        if bid is not None and ask is not None:
            if buy_or_sell == "BUY":
                price= round(ask,5)
            else:
                price= round(bid,5)

        else :
            cp = self.provider.current_price(self.config["orders_config"]["symbol"], buy_or_sell)
            price= round(cp,5)
        
        return price



class OrderState(ABC):

    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager

    @order_manager.setter
    def order_manager(self, order_manager: OrderManager) -> None:
        self._order_manager = order_manager

    @abstractmethod
    def on_tick(self) -> None:
        pass
    
    @abstractmethod
    def get_status(self) -> OrderStates:
        pass


class InitState(OrderState):
    def on_tick(self) -> None:
        try:
            # try to place active order
            # change price for actuall price
            # calculate actuall sl based on price

            self.order_manager.transition_to(ActivState())
        except:
            self.order_manager.transition_to(ErrorState())

    def get_status() -> OrderStates:
        return OrderStates.INIT


class ActivState(OrderState):
    def on_tick(self) -> None:
        # should process order
        # we should add strategy for tariling stop and normal order
        # here we 
        print("ConcreteStateB handles request1.")

    def process_order(self) -> None:
        self.order_manager.transition_to(ErrorState())

    def get_status(self) -> OrderStates:
        return OrderStates.ACTIVE


class ErrorState(OrderState):
    try_count: int = 0

    def on_tick(self) -> None:
        self.try_count += 1
        
        try:
            # check try_count if higher than 9 should send error
            # if it was lower than 9 should try to palce order
            # if order placed succecfully change state
            # 

            print("ConcreteStateB handles request1.")
        
        except:
            print("ConcreteStateB handles request1.")
    
    def process_order(self) -> None:
        pass
        # self.order_manager.transition_to(ConcreteStateA())
    
    def get_status(self) -> OrderStates:
        return OrderStates.FAILED
