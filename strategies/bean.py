import uuid
from enum import IntEnum
import time
from publisher import TickListener
from trading_platform import Platform
from typing import List , Optional, TypedDict , Dict, Tuple, Any


class BoxErrorStatus(IntEnum):
    START_ERROR=0
    ACTIVE_ORDER_ERROR=1
    PENDING_ORDER_ERROR=2
    CLOSE_ORDER_ERROR=3
    STATE_MANAGER_ERROR=4
    PROCESS_SELL_ORDER=5
    PROCESS_BUY_ORDER=6


class OrderDetails(TypedDict):
    index: int
    buy_or_sell: str
    ticket: Optional[str]
    symbol: str
    volume: float
    sl: float
    tp: float
    price: float

class BeanStrategy(TickListener):
    symbol: str
    provider: type[Platform]
    first_order_signal: str
    max_order: int
    logger: Any
    try_count: int
    base_lot: float
    growth_factor: float
    base_index: int
    lot_pips: Dict[int, float]
    lock: bool
    id: uuid.UUID
    orders_list: List[Optional[OrderDetails]]
    box: Dict[str , int]
    
    # constructor
    def __init__(self, provider, logger:Any ,symbol:str , max_order=22 , first_order_signal="BUY" , try_count=9) -> None:
        
        # Constatnt TODO: make their name with underscore
        self.symbol = symbol
        self.provider = provider
        self.first_order_signal = first_order_signal
        self.max_order = max_order
        self.logger = logger
        self.try_count = try_count
        
        # Define constants for volume calculation
        self.base_lot = 0.1
        self.growth_factor = 1.3  # Multiplier for exponential volume growth
        self.base_index = 3  # Index from which exponential growth starts
        self.lot_pips = {
            13: 8.6,
            14: 8.6,
            15: 8.6,
            16: 8.6,
            17: 8.7,
            18: 8.7,
            19: 8.8,
            20: 8.8,
            21: 8.7,
            22: 8.7
        }

        '''
        if index == 13 : lot_pip = 8.6
        elif index == 14 : lot_pip = 7.3
        elif index == 15 : lot_pip = 7.8
        elif index == 16: lot_pip = 7.5
        elif index == 17 : lot_pip = 7.7
        elif index == 18 : lot_pip = 8.1
        elif index == 19 : lot_pip = 8.9
        elif index == 20 : lot_pip = 8.7
        '''

        # variable TODO: put them in state status
        self.lock = True
        self.orders_list = [None] #TODO: make type for this
        self.box = {
            "id":uuid.uuid4(),
            "active_index": 1,
        }


    # public method
    def run(self) -> None:
        # TODO: check time , if market is close or if near to close dont run 
        self.logger.debug("Starting New Box ...")
        self.logger.debug("Reseting State ...")
        self.__reset_state()
        self.__start()
        self.lock = False
        self.logger.debug("New Box Started Successfully !")

    def on_tick(self , tick: Tuple[float, float]) -> None:

        if self.lock : return

        self.__state_manager(bid = tick[1] , ask = tick[2])    
    
    def get_symbol(self) -> str:
        return self.symbol


    # Manage state    
    def __start(self) -> None:
        """
        Start the trading box by calculating pre-orders and placing initial orders.
        Handles exceptions and logs the progress at each step.
        """

        try:
            self.logger.info("Placing First Active Order ...")
            self.__place_active_order()
                        
        except Exception as e:
            self.logger.error(e)
            self.run()

    def __reset_state(self) -> None:
        """
        Reset the trading box state, preparing for a new cycle or initialization.
        """
       
        self.lock = True
        self.orders_list=[None]
        self.box["id"] = uuid.uuid4()
        self.box["active_index"] = 1
        
        self.logger.info("State Reseted !")

    def __update_state(self)-> None:
        """
        Update the indices of the active and pending orders in the trading box.
        """

        self.box["active_index"] += 1
        self.logger.info("State Updated !")

    def __state_manager(self, bid: float, ask: float) -> None:
        """
        Manage the state of orders based on current market prices.

        Parameters:
            bid (float): The current bid price.
            ask (float): The current ask price.
        """
        active_index = self.box["active_index"]
        active_order = self.orders_list[active_index]
        try:
            box_done = self.__process_order(active_order, bid, ask)
            if box_done : self.run()
            else: return
        
        except Exception as e:
            self.logger.error(e)
            self.run()


    # Process Orders
    def __process_order(self, order: OrderDetails, bid: float, ask: float) -> bool:
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
            raise Exception({
                "code": BoxErrorStatus.STATE_MANAGER_ERROR,
                "details": e
            })
   
    def __process_buy_order(self, order: OrderDetails, bid: float) -> bool:
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
                return True
            
            elif bid <= order["sl"]:
                self.logger.warning("SL Touched For Buy Position...")
                self.__update_state()
                self.__place_active_order()
                return False
            
        except Exception as e :
            raise Exception({
                "code": BoxErrorStatus.PROCESS_BUY_ORDER,
                "details": e
            })

    def __process_sell_order(self, order: OrderDetails, ask: float) -> bool:
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
                return True

            elif ask >= order["sl"]:
                self.logger.warning("SL Touched For Sell Position...")
                self.__update_state()
                self.__place_active_order()
                return False

        except Exception as e: 
            raise Exception({
                "code": BoxErrorStatus.PROCESS_SELL_ORDER,
                "details": e
            })

    
    #  Calculate Orders
    def __calculate_order(self , i) -> None :
        """
        Calculate all preliminary orders based on the strategy parameters and update the orders_list list.
        """

        buy_or_sell = self.__calculate_buy_or_sell(i)
        volume = self.__calculate_vol(i)
        price, stop_loss, take_profit = self.__calculate_order_details(i, buy_or_sell)

        request: OrderDetails = {
            "index": i,
            "buy_or_sell": buy_or_sell,
            "ticket": None,
            "symbol": self.symbol,
            "volume": volume,
            "sl": stop_loss,
            "tp": take_profit,
            "price": price,
        }
        self.orders_list.insert(i,request)
        print(request)
        self.logger.info("Order Calculated !")
 
    def __calculate_order_details(self, index: int, buy_or_sell: str) -> Tuple[float, float, float]:
        """
        Calculate the price, stop loss, and take profit for a given order based on its index and type.

        Parameters:
            index (int): The index of the order.
            buy_or_sell (str): Indicates whether the order is a 'BUY' or 'SELL'.

        Returns:
            Tuple[float, float, float]: A tuple containing the price, stop loss, and take profit values.
        """
        price = self.__calculate_current_price(buy_or_sell)
        tp, sl = self.__calculate_tp_sl(price, buy_or_sell, index)

        return price, sl, tp
    
    def __calculate_buy_or_sell(self , index: int) -> str:
        """
        Determine whether to buy or sell based on the order index and the initial trading signal.

        Parameters:
            index (int): The index of the order to evaluate.

        Returns:
            str: 'BUY' or 'SELL' depending on the order index and initial signal.
        """
        signal = self.first_order_signal
        start_with_buy =  signal == "BUY"

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

        if index < 4:
            return self.base_lot
        else:
            # Calculate the exponent based on how far the index is from the base index
            n = index - self.base_index
            return round((pow(self.growth_factor, n) * self.base_lot), 2)

    def __calculate_tp_sl(self, cp: float, buy_or_sell: str, index: Optional[int] = None) -> Tuple[float, float]:
        """
        Calculate the take-profit and stop-loss prices.

        Parameters:
            cp (float): Current price for the order.
            buy_or_sell (str): 'BUY' or 'SELL' order.
            index (Optional[int]): The index of the order, used to determine specific adjustments.

        Returns:
            Tuple[float, float]: The calculated take-profit and stop-loss prices.
        """

        pip_uint = self.provider.get_symbol_pip_unit(self.symbol)

        if index < 13: tp_pip = round(pip_uint * 10 ,5) 
        else: tp_pip = round(pip_uint * self.__calculate_tp(index) ,5) 
        sl_pip = pip_uint * 2
        
        if buy_or_sell == "SELL":
            tp_price =cp - tp_pip
            sl_price = cp + sl_pip

        else:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        final_tp_price = round(tp_price , 5)
        final_sl_price = round(sl_price,5)

        return (final_tp_price,final_sl_price )

    def __calculate_current_price(self, buy_or_sell: str) -> float:
        """
        Fetch the current price from the trading platform.

        Parameters:
            buy_or_sell (str): 'BUY' or 'SELL' to possibly influence how the price is fetched.

        Returns:
            float: The current market price for the specified type.
        """
        current_price = self.provider.current_price( self.symbol, buy_or_sell)
        
        return round(current_price,5)
    
    def __calculate_tp(self, index: int) -> float:
        """
        Fetch the predefined take profit pip value based on the order index.

        Parameters:
            index (int): The index of the order.

        Returns:
            float: The take profit pip value.

        Raises:
            ValueError: If no predefined value exists for the given index.
        """
        if index in self.lot_pips:
            return self.lot_pips[index]
        else:
            self.logger.error(f"No TP data for index: {index}")
            raise ValueError(f"No take profit data available for index {index}")


    # Oder actions
    def __place_active_order(self)  -> None:
        """
        Attempt to place the active order up to a maximum number of tries defined by try_count.
        Logs the outcome of each attempt and handles failures.
        """

        for attempt in range(self.try_count):
            active_index = self.box["active_index"]
            self.__calculate_order(active_index)
            active_order = self.orders_list[active_index]
            
            symbol = active_order["symbol"]
            volume = active_order["volume"]
            buy_or_sell = active_order["buy_or_sell"]
            sl = active_order["sl"]
            tp = active_order["tp"]
            price = active_order["price"]

            result = self.provider.place_bracket_order(symbol, volume, buy_or_sell, sl, tp, price)
            if result["done"]:
                self.logger.info("Active order placed successfully !")
                active_order["ticket"] = result["ticket"]
                return

            else:
                self.logger.error(f"Attempt {attempt+1}: Failed to place active order: {result['comment']}")
                self.logger.debug("trying one more time")
                time.sleep(0.3)
        
        # Restart the entire process if unable to place the order after all attempts
        self.logger.error("Maximum retries reached for placing active order. Restarting Box...")
        raise Exception({
            "code":BoxErrorStatus.ACTIVE_ORDER_ERROR,
            "details": result['comment'] 
        }) 