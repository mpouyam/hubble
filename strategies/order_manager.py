from enum import StrEnum
import time
from typing import Tuple , Optional , TypedDict
from utils import now_time_iran
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
        self.orders:list[OrderDetails] = []
        self.active_order: OrderDetails = None


    
    def _reset_order_state(self):
        self.orders = []
        self.active_order = None
    
    
    # Oder actions
    def _place_order(self , order_number: int ,bid:float , ask :float) -> OrderDetails:
        for attempt in range(self.config["orders_config"]["try_count"]):
            if attempt == 0 :
                self._calculate_order(order_number , bid , ask)
            else:
                self._calculate_order(order_number)

            
            self.active_order["spread"] = round(ask - bid , 5)


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


        for attempt in range(self.config["orders_config"]["try_count"]):

            result = self.provider.close_position(active_order_ticket , self.config["orders_config"]["symbol"])
            if result["done"]:
                self.active_order["state"] = OrderState.CLOSED
                self.active_order["ended_at"] = now_time_iran(self.clock)

                self.__add_to_orders(self.active_order)
                return self.active_order

            else:
                self.logger.error(f"Attempt {attempt+1}: Failed To Close Active Order: {result['comment']}")
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
            self.active_order["ended_at"] = now_time_iran(self.clock)
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
    def _calculate_order(self , order_number , bid=None , ask=None) -> None:
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
            "started_at": now_time_iran(self.clock),
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
        if index in self.config["orders_config"]["static_vol"]:
            return self.config["orders_config"]["static_vol"][index]

        else:
            n = list(self.config["orders_config"]["static_vol"].keys())[-1] if self.config["orders_config"]["static_vol"] else 0
            return round(
                (
                    pow(self.config["orders_config"]["growth_factor"], index - n)
                    * self.config["orders_config"]["base_lot"]
                ),
                2,
            )

    def __calculate_tp_sl(self, cp: float, buy_or_sell: str , index: int) -> Tuple[float, float]:
        static_tp = self.config["orders_config"].get("static_tp", {})
        static_sl = self.config["orders_config"].get("static_sl", {})
        
        tp_limit = static_tp.get(index, self.config["orders_config"]["tp_limit"])
        sl_limit = static_sl.get(index, self.config["orders_config"]["sl_limit"])
        
        pip_unit = self.config["orders_config"]["pip_unit"]

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
