import datetime
import time
import uuid
from enum import IntEnum
from typing import Any, Dict, Optional, Tuple, TypedDict

import pytz

from publisher import TickListener
from trading_platform import Platform


class BoxErrorStatus(IntEnum):
    START_ERROR = 0
    ACTIVE_ORDER_ERROR = 1
    PENDING_ORDER_ERROR = 2
    CLOSE_ORDER_ERROR = 3
    STATE_MANAGER_ERROR = 4
    PROCESS_SELL_ORDER = 5
    PROCESS_BUY_ORDER = 6


class StrategyState(IntEnum):
    INIT = 0
    ON = 1
    OFF = 2
    OFFF = 3


class BoxState(IntEnum):
    INIT = 0
    RUNNING = 1
    RETRYING = 2
    FINISHED = 3


class OrderState(IntEnum):
    INIT = 0
    ACTIVE = 1
    DONE = 2


class OrderStatus(IntEnum):
    SL = 0
    TP = 1
    NOTHING = 2


class OrderDetails(TypedDict):
    index: int
    buy_or_sell: str
    ticket: Optional[str]
    symbol: str
    volume: float
    sl: float
    tp: float
    price: float
    state: OrderState
    status: OrderStatus
    started_at: str
    ended_at: str


class BeanStrategy(TickListener):
    symbol: str
    provider: type[Platform]
    logger: Any
    try_count: int
    box: Dict[str, Any]

    # constructor
    def __init__(
        self, provider: Platform, logger: Any, symbol: str, try_count: int = 9
    ) -> None:
        self.symbol = symbol
        self.provider = provider
        self.logger = logger
        self.try_count = try_count
        self.box = self.initialize_box()

    def initialize_box(self) -> Dict[str, Any]:
        return {
            "id": uuid.uuid4(),
            "state": BoxState.INIT,
            "config": self.initialize_config(),
            "orders": [None],
            "first_order_signal": "BUY",
            "active_index": 1,
            "started_at": self.now_time(),
            "ended_at": None,
        }

    def initialize_config(self) -> Dict[str, Any]:
        return {
            "pip_uint": self.provider.get_symbol_pip_unit(self.symbol),
            "tp_limit": 10,
            "sl_limit": 2,
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
        }

    # public method
    def on_tick(self, tick: Tuple[float, float]) -> None:
        self.__state_manager(bid=tick[1], ask=tick[2])

    def get_symbol(self) -> str:
        return self.symbol

    # Manage state
    def __state_manager(self, bid: float, ask: float) -> None:
        """
        Manage the state of orders based on current market prices.

        Parameters:
            bid (float): The current bid price.
            ask (float): The current ask price.
        """
        if self.box["state"] == BoxState.INIT:
            active_order = self.__place_order(bid, ask)
            self.box["orders"].append(active_order)
            self.box["state"] = BoxState.RUNNING
            return

        elif self.box["state"] == BoxState.RUNNING:
            active_order = self.box["orders"][-1]
            if active_order is not None:
                order_status = self.__process_order(active_order, bid, ask)
                self.__handle_active_order(order_status, active_order)
                if order_status == OrderStatus.SL:
                    active_order = self.__place_order(bid, ask)
                    self.box["orders"].append(active_order)
                    return
                elif order_status == OrderStatus.TP:
                    self.__reset_state()
                else:
                    return

            else:
                self.__reset_state()
                return
        elif self.box["state"] == BoxState.FINISHED:
            # TODO: persist data
            self.__reset_state()
            return

    def __handle_active_order(self, orderStatus: OrderStatus, order: Dict) -> bool:
        if orderStatus != OrderStatus.NOTHING:
            order["state"] = OrderState.DONE
            order["status"] = orderStatus
            order["ended_at"] = self.now_time()
            self.box["state"] = (
                BoxState.FINISHED if orderStatus == OrderStatus.TP else BoxState.RUNNING
            )
            self.box["ended_at"] = (
                self.now_time() if orderStatus == OrderStatus.TP else None
            )
            self.box["active_index"] = (
                self.box["active_index"]
                if orderStatus == OrderStatus.TP
                else self.box["active_index"] + 1
            )
            if orderStatus == OrderStatus.TP:
                self.__reset_state()
            else:
                return
        else:
            return

    def __reset_state(self):
        self.box = self.initialize_box()

    # Process Orders
    def __process_order(
        self, order: OrderDetails, bid: float, ask: float
    ) -> OrderStatus:
        """
        Process an order based on the current market prices.

        Parameters:
            order (OrderDetails): The order details to process.
            bid (float): The current bid price of the asset.
            ask (float): The current ask price of the asset.
        """
        try:
            result = None
            if order["buy_or_sell"] == "BUY":
                result = self.__process_buy_order(order, bid)
            else:
                result = self.__process_sell_order(order, ask)

            return result

        except Exception as e:
            raise Exception({"code": BoxErrorStatus.STATE_MANAGER_ERROR, "details": e})

    def __process_buy_order(self, order: OrderDetails, bid: float) -> OrderStatus:
        """
        Execute logic for a buy order based on the current bid price.

        Parameters:
            order (OrderDetails): The buy order details to process.
            bid (float): The current bid price of the asset.

        Actions:
            - If the bid price meets or exceeds the take profit (tp) value, close the pending order.
            - If the bid price falls to or below the stop loss (sl) value, update the state and place a pending order.
        """
        try:
            if bid >= order["tp"]:
                self.logger.critical("TP Touched For Buy Position...")
                return OrderStatus.TP

            elif bid <= order["sl"]:
                self.logger.warning("SL Touched For Buy Position...")
                return OrderStatus.SL
            else:
                return OrderStatus.NOTHING

        except Exception as e:
            raise Exception({"code": BoxErrorStatus.PROCESS_BUY_ORDER, "details": e})

    def __process_sell_order(self, order: OrderDetails, ask: float) -> OrderStatus:
        """
        Execute logic for a sell order based on the current ask price.

        Parameters:
            order (OrderDetails): The sell order details to process.
            ask (float): The current ask price of the asset.

        Actions:
            - If the ask price meets or falls below the take profit (tp) value, close the pending order.
            - If the ask price rises to or above the stop loss (sl) value, update the state and place a pending order.
        """
        try:
            if ask <= order["tp"]:
                self.logger.critical("TP Touched For Sell Position...")
                return OrderStatus.TP

            elif ask >= order["sl"]:
                self.logger.warning("SL Touched For Sell Position...")
                return OrderStatus.SL
            else:
                return OrderStatus.NOTHING

        except Exception as e:
            raise Exception({"code": BoxErrorStatus.PROCESS_SELL_ORDER, "details": e})

    #  Calculate Orders
    def __calculate_order(self, price: Tuple[float, float], index: int) -> OrderDetails:
        """
        Calculate all preliminary orders based on the strategy parameters and update the box["orders"] list.
        """

        buy_or_sell = self.__calculate_buy_or_sell(index)
        current_price = price[0] if buy_or_sell == "BUY" else price[1]
        volume = self.__calculate_vol(index)
        stop_loss, take_profit = self.__calculate_tp_sl(current_price, buy_or_sell)

        order: OrderDetails = {
            "index": index,
            "buy_or_sell": buy_or_sell,
            "ticket": None,
            "symbol": self.symbol,
            "volume": volume,
            "sl": stop_loss,
            "tp": take_profit,
            "price": current_price,
            "state": OrderState.INIT,
            "status": OrderStatus.NOTHING,
            "started_at": self.now_time(),
            "ended_at": None,
        }

        self.logger.info("Order Calculated !")
        return order

    def __calculate_buy_or_sell(self, index: int) -> str:
        """
        Determine whether to buy or sell based on the order index and the initial trading signal.

        Parameters:
            index (int): The index of the order to evaluate.

        Returns:
            str: 'BUY' or 'SELL' depending on the order index and initial signal.
        """
        signal = self.box["first_order_signal"]
        start_with_buy = signal == "BUY"

        if start_with_buy:
            return "BUY" if index % 2 != 0 else "SELL"
        else:
            return "SELL" if index % 2 == 0 else "BUY"

    def __calculate_vol(self, index: int) -> float:
        """
        Calculate the trading volume based on the order index.
        The volume for indices less than 4 is the base lot size.
        For indices 4 and above, the volume increases exponentially based on the growth factor.

        Parameters:
            index (int): The index of the order for which volume is being calculated.

        Returns:
            float: The calculated volume based on the index.
        """

        if index in self.box["config"]["static_vol"]:
            return self.box["config"]["static_vol"][index]

        else:
            # Calculate the exponent based on how far the index is from the base index
            n = index - self.box["config"]["base_index"]
            return round(
                (
                    pow(self.box["config"]["growth_factor"], n)
                    * self.box["config"]["base_lot"]
                ),
                2,
            )

    def __calculate_tp_sl(self, cp: float, buy_or_sell: str) -> Tuple[float, float]:
        """
        Calculate the take-profit and stop-loss prices.

        Parameters:
            cp (float): Current price for the order.
            buy_or_sell (str): 'BUY' or 'SELL' order.
            index (Optional[int]): The index of the order, used to determine specific adjustments.

        Returns:
            Tuple[float, float]: The calculated take-profit and stop-loss prices.
        """
        pip_unit = self.box["config"]["pip_uint"]
        tp_pip = pip_unit * self.box["config"]["tp_limit"]
        sl_pip = pip_unit * self.box["config"]["sl_limit"]

        if buy_or_sell == "SELL":
            tp_price = cp - tp_pip
            sl_price = cp + sl_pip

        else:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        final_tp_price = round(tp_price, 5)
        final_sl_price = round(sl_price, 5)

        return (final_tp_price, final_sl_price)

    # Oder actions
    # Oder actions
    def __place_order(self, bid, ask) -> OrderDetails:
        """
        Attempt to place the active order up to a maximum number of tries defined by try_count.
        Logs the outcome of each attempt and handles failures.
        """

        for attempt in range(self.try_count):
            active_index = self.box["active_index"]
            order = self.__calculate_order((bid, ask), active_index)

            symbol = order["symbol"]
            volume = order["volume"]
            buy_or_sell = order["buy_or_sell"]
            sl = order["sl"]
            tp = order["tp"]
            price = order["price"]

            result = self.provider.place_bracket_order(
                symbol, volume, buy_or_sell, sl, tp, price
            )
            if result["done"]:
                self.logger.info("Active order placed successfully !")
                order["ticket"] = result["ticket"]
                order["state"] = OrderState.ACTIVE
                return order

            else:
                self.logger.error(
                    f"Attempt {attempt+1}: Failed to place active order: {result['comment']}"
                )
                self.logger.debug("trying one more time")
                time.sleep(0.3)

        # Restart the entire process if unable to place the order after all attempts
        self.logger.error(
            "Maximum retries reached for placing active order. Restarting Box..."
        )
        raise Exception(
            {"code": BoxErrorStatus.ACTIVE_ORDER_ERROR, "details": result["comment"]}
        )

    # utils
    def now_time():
        return (
            datetime.utcnow()
            .replace(tzinfo=pytz.utc)
            .astimezone(pytz.timezone("Asia/Tehran"))
            .strftime("%Y-%m-%d %H-%M-%S"),
        )
