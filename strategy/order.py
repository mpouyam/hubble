from dataclasses import replace
from typing import Tuple
from abc import ABC, abstractmethod

from trading_platform import Platform
from type import OrderRecipes, OrderErrorStatus, OrderStatus, OrderSignal, Order, OrderDirection
from utils import format_gmt_time


class OrderState(ABC):
    _order_manager: 'OrderManager'

    @property
    def order_manager(self) -> 'OrderManager':
        return self._order_manager

    @order_manager.setter
    def order_manager(self, order_manager: 'OrderManager') -> None:
        self._order_manager = order_manager

    @abstractmethod
    def on_tick(self, tick) -> None:
        pass

    @abstractmethod
    def on_signal(self, signal: OrderSignal) -> None:
        pass

    @abstractmethod
    def get_prototype(self) -> Order:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass


class OrderManager:
    _state: OrderState = None

    def __init__(self, provider: Platform, logger, orderRecipes: OrderRecipes):
        self.provider = provider
        self.logger = logger

        self.symbol = orderRecipes.symbol
        self.pip_unit = orderRecipes.unit
        self.direction = orderRecipes.direction
        self.volume = orderRecipes.volume
        self.tp_limit = orderRecipes.tp
        self.sl_limit = orderRecipes.sl

        self.ticket = None
        self.price = None
        self.sl_price = None
        self.tp_price = None
        self.started_at = None
        self.ended_at = None
        self.status = OrderStatus.NOTHING
        self.error = None
        self.error_status: OrderErrorStatus = OrderErrorStatus.NONE

        self.transition_to(Placing(self.get_prototype()))

    def transition_to(self, state: OrderState) -> None:
        self.logger.warning(f"ORDER Transition To: {state.__class__.__name__}")
        self._state = state
        self._state.order_manager = self

    def on_tick(self, tick) -> None:
        self.logger.info(f"\n Layer: {self.__class__.__name__}\n State: {self._state.__class__.__name__}\n Tick : {tick}")
        self._state.on_tick(tick)

    def on_signal(self, signal: OrderSignal) -> None:
        if signal not in OrderSignal:
            self.logger.error(f"Invalid Signal Received: {signal}")
            return
        else:
            self.logger.critical(f"\n Layer: {self.__class__.__name__}\n State: {self._state.__class__.__name__}\n Signal : {signal}")
            self._state.on_signal(signal)

    def is_done(self) -> bool:
        return self._state.is_done()

    def get_prototype(self) -> Order:
        if self._state is None:
            return Order(
                symbol=self.symbol,
                pip_unit=self.pip_unit,
                ticket=self.ticket,
                status=self.status,
                direction=self.direction,
                volume=self.volume,
                price=self.price,
                tp_limit=self.tp_limit,
                sl_limit=self.sl_limit,
                tp_price=self.tp_price,
                sl_price=self.sl_price,
                started_at=self.started_at,
                ended_at=self.ended_at,
                error=self.error,
                error_status=self.error_status
            )
        else:
            return self._state.get_prototype()



class Placing(OrderState):
    try_count = 1
    _order: Order

    def __init__(self, order: Order):
        self._order = replace(order)

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: OrderSignal) -> None:
        if signal == OrderSignal.CLOSE:
            if self._order.ticket is not None:
                self.order_manager.transition_to(Closing(self._order))
            else:
                self.order_manager.transition_to(Final(self._order))

    def on_tick(self, tick) -> None:
        ts = tick[0]
        bid = tick[1]
        ask = tick[2]

        direction = self._order.direction
        price = ask if direction == OrderDirection.BUY else bid

        try:
            tp, sl = self.__calculate_limit_prices(price)
            active_order = self.__place_order(price, sl, tp)
            self.__modify_inward_order(active_order["ticket"], active_order["price"], tp, sl, ts)

            # check if there is a difference between actual price and placed price
            if active_order["price"] != price:
                self.order_manager.transition_to(Modifying(self._order))
            else:
                self.order_manager.transition_to(Processing(self._order))

        except Exception as e:
            if self.try_count < 9:
                self.try_count += 1
                return
            else:
                self.order_manager.logger.error("Maximum Retries Reached")
                self._order.error = e
                self._order.error_status = OrderErrorStatus.PLACING
                self.order_manager.transition_to(Final(self._order))

    def get_prototype(self) -> Order:
        return self._order

    def __calculate_limit_prices(self, price: float) -> Tuple[float, float]:

        sl_pip = self._order.pip_unit * self._order.sl_limit
        tp_pip = self._order.pip_unit * self._order.tp_limit

        sl_price = None
        tp_price = None

        if self._order.direction == OrderDirection.SELL:
            sl_price = price + sl_pip
            tp_price = price - tp_pip

        elif self._order.direction == OrderDirection.BUY:
            sl_price = price - sl_pip
            tp_price = price + tp_pip

        return round(tp_price, 5), round(sl_price, 5)

    def __place_order(self, price: float, sl: float, tp: float):

        symbol = self._order.symbol
        volume = self._order.volume
        direction = self._order.direction
        action = None

        if direction == OrderDirection.BUY:
            action = self.order_manager.provider.place_buy_order

        elif direction == OrderDirection.SELL:
            action = self.order_manager.provider.place_sell_order

        result = action(symbol, volume, price, sl, tp)

        if result["done"]:
            self.order_manager.logger.info("Active order placed successfully !")
            return result

        else:
            self.order_manager.logger.error(
                f"Attempt {self.try_count}: Failed to place active order: {result['comment']}")
            raise Exception(result["comment"])

    def __modify_inward_order(self, ticket: int, price: float, tp: float, sl: float, ts: int) -> None:
        self._order.ticket = ticket
        self._order.price = price
        self._order.sl_price = sl
        self._order.tp_price = tp
        self._order.started_at = format_gmt_time(ts)


class Modifying(OrderState):
    try_count = 1
    _order: Order

    def __init__(self, order: Order):
        self._order = replace(order)

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: OrderSignal) -> None:
        if signal == OrderSignal.CLOSE:
            self.order_manager.transition_to(Closing(self._order))

    def on_tick(self, tick) -> None:
        if self._order.ticket is None:
            self.order_manager.transition_to(Final(self._order))
            return

        tp, sl = self.__calculate_limit_prices()

        try:
            self.__modify_outward_order(sl, tp)
            self.__modify_inward_order(tp, sl)
            self.order_manager.transition_to(Processing(self._order))

        except Exception as e:
            if self.try_count < 9:
                self.try_count += 1
                return
            else:
                self.order_manager.logger.error("Maximum Retries Reached")
                self._order.error = e
                self._order.error_status = OrderErrorStatus.MODIFYING
                self.order_manager.transition_to(Processing(self._order))

    def get_prototype(self) -> Order:
        return self._order

    def __calculate_limit_prices(self) -> Tuple[float, float]:

        sl_pip = self._order.pip_unit * self._order.sl_limit
        tp_pip = self._order.pip_unit * self._order.tp_limit

        sl_price = None
        tp_price = None

        if self._order.direction == OrderDirection.SELL:
            sl_price = self._order.price + sl_pip
            tp_price = self._order.price - tp_pip

        elif self._order.direction == OrderDirection.BUY:
            sl_price = self._order.price - sl_pip
            tp_price = self._order.price + tp_pip

        return round(tp_price, 5), round(sl_price, 5)

    def __modify_outward_order(self, sl: float, tp: float) -> None:
        ticket = self.order_manager.ticket
        self.order_manager.provider.modify_tp_sl_order(ticket, sl, tp)

    def __modify_inward_order(self, sl: float, tp: float) -> None:
        self._order.sl_price = sl
        self._order.tp_price = tp


class Processing(OrderState):
    _order: Order

    def __init__(self, order: Order):
        self._order = replace(order)

    def is_done(self) -> bool:
        return False

    def on_signal(self, signal: OrderSignal) -> None:
        order = self.get_prototype()

        if signal is OrderSignal.CLOSE:
            self.order_manager.transition_to(Closing(order))
        return

    def on_tick(self, tick) -> None:
        bid = tick[1]
        ask = tick[2]

        order_status = self.__process_order(bid, ask)

        if order_status != OrderStatus.NOTHING:
            self._order.status = order_status
            self.order_manager.transition_to(Final(self._order))

        return

    def get_prototype(self) -> Order:
        return self._order

    # Process Orders
    def __process_order(self, bid: float, ask: float) -> OrderStatus:
        order_status = OrderStatus.NOTHING

        if self._order.direction == OrderDirection.BUY:
            order_status = self.__process_buy_order(bid)

        elif self._order.direction == OrderDirection.SELL:
            order_status = self.__process_sell_order(ask)

        return order_status

    def __process_buy_order(self, bid: float) -> OrderStatus:

        if bid >= self._order.tp_price:
            self.order_manager.logger.critical("TP Touched For Buy Position...")
            return OrderStatus.TP

        elif bid <= self._order.sl_price:
            self.order_manager.logger.warning("SL Touched For Buy Position...")
            return OrderStatus.SL

        else:
            return OrderStatus.NOTHING

    def __process_sell_order(self, ask: float) -> OrderStatus:
        if ask <= self._order.tp_price:
            self.order_manager.logger.critical("TP Touched For Sell Position...")
            return OrderStatus.TP

        elif ask >= self._order.sl_price:
            self.order_manager.logger.warning("SL Touched For Sell Position...")
            return OrderStatus.SL

        else:
            return OrderStatus.NOTHING


class Closing(OrderState):
    try_count = 1
    _order: Order

    def __init__(self, order: Order):
        self._order = replace(order)

    def is_done(self) -> bool:
        return False

    def on_tick(self, tick) -> None:
        ts = tick[0]

        if self._order.ticket is None:
            self.order_manager.transition_to(Final(self._order))
            return

        try:
            self.__close_order()
            self.__modify_inward_order()
            self.order_manager.transition_to(Final(self._order))

        except Exception as e:
            if self.try_count < 9:
                self.try_count += 1
                return
            else:
                self.order_manager.logger.error("Maximum Retries Reached")
                self._order.error = e
                self._order.error_status = OrderErrorStatus.CLOSING
                self.order_manager.transition_to(Final(self._order))

    def on_signal(self, signal: OrderSignal) -> None:
        return

    def get_prototype(self) -> Order:
        return self._order

    def __close_order(self) -> None:

        ticket = self._order.ticket
        symbol = self._order.symbol
        result = self.order_manager.provider.close_position(ticket, symbol)

        if not result["done"]:
            self.order_manager.logger.error(
                f"Attempt {self.try_count}: Failed To Close Active Order: {result['comment']}")
            raise Exception(result["comment"])

    def __modify_inward_order(self) -> None:
        self._order.status = OrderStatus.CLOSED


class Final(OrderState):
    _order: Order
    finished = False

    def __init__(self, order: Order):
        self._order = replace(order)

    def get_prototype(self) -> Order:
        return self._order

    def on_signal(self, signal: OrderSignal) -> None:
        return

    def on_tick(self, tick) -> None:
        self._order.ended_at = format_gmt_time(tick[0])
        self.finished = True
        return

    def is_done(self) -> bool:
        return self.finished
