from enum import StrEnum , Enum
import time
from typing import Any, Dict, Tuple , Optional , TypedDict
from trading_platform import Platform
from utils import now_time_iran
import uuid
import json
from abc import abstractmethod
from publisher import TickListener


class OrderStatus(StrEnum):
    SL = "SL"
    TP = "TP"
    NOTHING = "NOTHING"

class OrderState(StrEnum):
    INIT = "INIT"
    ACTIVE = "ACTIVE"
    DONE =  "DONE"
    CLOSED = "CLOSED"
    FAILED = "FAILED"

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


class OrderManager(TickListener):
    def __init__(self):
        self.config = self.__initialize_config()
        self.orders:list[OrderDetails] = []
        self.active_order: OrderDetails = None

    def __initialize_config(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "first_order_signal": "BUY",
            "pip_unit": self.provider.get_symbol_pip_unit(self.symbol),
            "try_count": 9,
            "tp_limit": 5,
            "sl_limit": 1,
            "base_lot": 0.1,
            "growth_factor": 1.3,
            "base_index": 11,
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
                11: 0.1,
            },
            "static_tp":{
                # 1: 10, its ineteger like tp_limit 
            },
            "static_sl":{
                # 1: 10, its ineteger like sl_limit 
            },
        }
    
    def _reset_order_state(self):
        self.orders = []
        self.active_order = None
    
    
    # Oder actions
    def _place_order(self , order_number: int) -> OrderDetails:

        for attempt in range(self.config["try_count"]):
            self.__calculate_order(order_number)

            symbol = self.active_order["symbol"]
            volume = self.active_order["volume"]
            buy_or_sell = self.active_order["buy_or_sell"]
            sl = self.active_order["sl"]
            tp = self.active_order["tp"]
            price = self.active_order["price"]

            result = self.provider.place_bracket_order(symbol, volume, buy_or_sell, sl, tp, price)
            
            if result["done"]:
                self.logger.info("Active order placed successfully !")
                self.active_order["ticket"] = result["ticket"]
                self.active_order["state"] = OrderState.ACTIVE
                return self.active_order

            else:
                self.logger.error(f"Attempt {attempt+1}: Failed to place active order: {result['comment']}")
                self.logger.debug("trying one more time")
                time.sleep(0.3)
        
        # Restart the entire process if unable to place the order after all attempts
        self.logger.error("Maximum retries reached for placing active order.")
        self.active_order["state"] = OrderState.FAILED
        self.active_order["error"] = result["comment"]
        self.__add_to_orders(self.active_order)
        return self.active_order
    
    def _close_order(self) -> None:
        if self.active_order is None:
            return

        active_order_ticket = self.active_order["ticket"]


        for attempt in range(self.config["try_count"]):

            result = self.provider.close_position(active_order_ticket)
            if result["done"]:
                self.active_order["state"] = OrderState.CLOSED
                self.active_order["ended_at"] = now_time_iran()

                self.__add_to_orders(self.active_order)
                return self.active_order

            else:
                self.logger.error(f"Attempt {attempt+1}: Failed To Place Active Order: {result['comment']}")
                self.logger.debug("Trying One More Time")
                time.sleep(0.3)
                self.logger.error("Maximum Retries Reached For Closing Active Order.")
        
        self.active_order["state"] = OrderState.FAILED
        self.active_order["error"] = result["comment"]
        self.__add_to_orders(self.active_order)
        
        return self.active_order
     
    def _get_orders_list(self) -> list[OrderDetails]:
        return self.orders

    def __add_to_orders(self , order:OrderDetails , index=None) -> None :
        if index is not None :
            self.orders.insert(index , order)

        else:
            self.orders.append(order)    

    # Process Orders
    def _process_order(self, bid: float, ask: float) -> OrderDetails:
        order_status = self.__process_buy_order(bid) if self.active_order["buy_or_sell"] == "BUY" else self.__process_sell_order(ask)

        if order_status != OrderStatus.NOTHING: 
            self.active_order["state"] = OrderState.DONE
            self.active_order["status"] = order_status
            self.active_order["ended_at"] = now_time_iran()
            self.active_order["spread"] = self.__calculate_spread(bid , ask)
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
    def __calculate_order(self , order_number) -> None:

        buy_or_sell = self.__calculate_buy_or_sell(order_number)
        current_price = self.__calculate_current_price(buy_or_sell)
        volume = self.__calculate_vol(order_number)
        take_profit , stop_loss  = self.__calculate_tp_sl(current_price, buy_or_sell , order_number)

        self.active_order = {
            "index": order_number,
            "buy_or_sell": buy_or_sell,
            "ticket": None,
            "symbol": self.config["symbol"],
            "volume": volume,
            "sl": stop_loss,
            "tp": take_profit,
            "price": current_price,
            "state": OrderState.INIT,
            "status": OrderStatus.NOTHING,
            "spread": None,
            "started_at": now_time_iran(),
            "ended_at": None,
            "error": None
        }

        my_dict_str = {str(key): str(value) if isinstance(value, (Enum, uuid.UUID)) else value for key, value in self.active_order.items()}

        print("----------------------")
        print(json.dumps(my_dict_str, indent=4))
        print("----------------------")

        self.logger.info("Order Calculated !")

    def __calculate_buy_or_sell(self, index: int) -> str:
        
        signal = self.config["first_order_signal"]
        start_with_buy = signal == "BUY"

        if start_with_buy:
            return "BUY" if index % 2 != 0 else "SELL"
        else:
            return "SELL" if index % 2 == 0 else "BUY"

    def __calculate_vol(self, index: int) -> float:

        if index in self.config["static_vol"]:
            return self.config["static_vol"][index]

        else:
            n = index - self.config["base_index"]
            return round(
                (
                    pow(self.config["growth_factor"], n)
                    * self.config["base_lot"]
                ),
                2,
            )

    def __calculate_tp_sl(self, cp: float, buy_or_sell: str , index: int) -> Tuple[float, float]:
        static_tp = self.config.get("static_tp", {})
        static_sl = self.config.get("static_sl", {})
        
        tp_limit = static_tp.get(index, self.config["tp_limit"])
        sl_limit = static_sl.get(index, self.config["sl_limit"])
        
        pip_unit = self.config["pip_unit"]

        tp_pip = pip_unit * tp_limit
        sl_pip = pip_unit * sl_limit

        if buy_or_sell == "SELL":
            tp_price = cp - tp_pip
            sl_price = cp + sl_pip

        else:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        final_tp_price = round(tp_price, 5)
        final_sl_price = round(sl_price, 5)

        return (final_tp_price, final_sl_price)

    def __calculate_current_price(self, buy_or_sell: str) -> float:

        current_price = self.provider.current_price(self.config["symbol"], buy_or_sell)
        
        return round(current_price,5)

    def __calculate_spread(self , bid , ask) -> float : 
        return ask - bid
