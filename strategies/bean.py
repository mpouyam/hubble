from mt5API import (
    close_position,
    current_price,
    get_symbol_pip_unit,
    place_bracket_order,
    place_pend_order,
)
# TODO : Error Handling
# 1- check market is open or not
# 2- if placing order was unsuccesful , what should we do :
#    - if error was in active order we should start from begining
#    - if pending 
class BeanStrategy:
    # constructor
    def __init__(self, provider, symbol) -> None:
        self.box = {
            "symbol": symbol,
            "active_index": 1,
            "pending_index": 2,
            "locked": True
        }
        self.provider = provider
        self.pre_orders = [None]
        self.max_order = 30


    # strategy public method
    def start(self):
        # TODO: check time , if market is close or if near to close dont run 
        print("New Box Is Starting ...")
        print("Calculating Pre Orders ...")
        self.__calculate_pre_orders()
        print("Placing First Active Order ...")
        self.__place_active_order()
        print("Placing First Pend Order ...")
        self.__place_pending_order()
        print("New Box Is Started Successfully !")
        
        self.__set_lock(False)

    def on_tick(self , tick):
        # If Box was locked we should not process any tick
        if self.box["locked"]: return
        else: self.__state_manager(tick)

    def get_symbol(self):
        return self.box["symbol"]


    # manage state
    def __set_lock(self , lock):
        self.box["locked"] = lock
    
    def __reset_state(self):
        self.pre_orders=[None]
        self.box["active_index"] = 1
        self.box["pending_index"] = 2
        self.box["locked"] = True
        print("State Reseted !")

    def __update_state(self):
        self.box["active_index"] += 1
        self.box["pending_index"] += 1
        print("State Updated !")

    def __state_manager(self , tick):
        # Lock the box until we process one tick
        self.__set_lock(True)
        
        active_order = self.pre_orders[self.box["active_index"]]
        active_sl = active_order["sl"]
        active_tp = active_order["tp"]
        active_direction = active_order["buy_or_sell"]
        bid = tick[1]
        ask = tick[2]

        if active_direction == "BUY" :
            # if price touched our active order tp -> close pending position -> reset state -> start again
            if bid >= active_tp :
                print("TP Touched For Buy Position ...")
                print("Closing Pending Order ...")
                self.__close_pending_order()
                print("Reseting State ...")
                self.__reset_state()
                print("Starting New Box ...")
                self.start()
            
            # if price touched active order sl -> our pending order activated -> change box state -> place pendig order -> box unlocked
            elif bid <= active_sl:
                print("SL Touched For Buy Position ...")
                print("Updating State ...")
                self.__update_state()
                print("Placing Next Pending Order ...")
                self.__place_pending_order()
                self.__set_lock(False)

            else:
                self.__set_lock(False)

        else: 
            # if price touched our active order tp -> close pending position -> reset state -> start again
            if ask <= active_tp :
                print("TP Touched For Sell Position")
                print("Closing Pending Order ...")
                self.__close_pending_order()
                print("Reseting State ...")
                self.__reset_state()
                print("Starting New Box ...")
                self.start()
            
            # if price touched active order sl -> our pending order activate -> change box state -> place pendig order -> box unlocked
            elif ask >= active_sl:
                print("SL Touched For Sell Position")
                print("Updating State ...")
                self.__update_state()
                print("Placing Next Pending Order ...")
                self.__place_pending_order()
                self.__set_lock(False)
            
            else:
                self.__set_lock(False)

   
    #  Calculate Orders
    def __calculate_pre_orders(self):
        for i in range(1 , self.max_order + 1):
            buy_or_sell = self.__buy_or_sell(i)
            vol = self.__calculate_vol(i)

            if i == 1 :
                cp = self.__calculate_current_price(buy_or_sell)
                tp , sl = self.__calcute_tp_sl(cp, buy_or_sell)

            elif  i == 2 :
                cp = self.pre_orders[1]["sl"]
                tp , sl = self.__calcute_tp_sl(cp, buy_or_sell)

            else :
                order = self.pre_orders[1] if i % 2 != 0 else self.pre_orders[2]
                tp = order["tp"]
                sl = order["sl"]
                cp = order["price"]

            request = {
                "index":i,
                "buy_or_sell": buy_or_sell,
                "ticket":None,
                "symbol": self.box["symbol"],
                "volume": vol,
                "sl": sl,
                "tp": tp,
                "price": cp,
            }

            self.pre_orders.append(request)
        
        print("Pre Orders Calculated !")
   
    def __buy_or_sell(self , index ):
        # we start with buy so odd numbers will be buy and even will be sell
        if index % 2 == 0:
            return "SELL"
        else:
            return "BUY"
    
    def __calculate_vol(self, index):
        c = 1.3
        lot = 0.1
        n = index - 3
        if index < 4:
            return lot
        else:
            return round((pow(c, n) * lot) , 2 )

    def __calcute_tp_sl(self, cp , buy_or_sell):
        pip_uint = get_symbol_pip_unit(self.provider, self.box["symbol"])

        tp_pip = pip_uint * 10
        sl_pip = pip_uint * 2
        
        if buy_or_sell == "SELL":
            tp_price =cp - tp_pip
            sl_price = cp + sl_pip

        else:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        return (round(tp_price , 5), round(sl_price,5))

    def __calculate_current_price(self , buy_or_sell):
        return current_price(self.provider, self.box["symbol"], buy_or_sell)

    
    # oder actions
    def __place_active_order(self):
        active_index = self.box["active_index"]
        active_order = self.pre_orders[active_index]

        symbol = active_order["symbol"]
        volume = active_order["volume"]
        buy_or_sell = active_order["buy_or_sell"]
        sl = active_order["sl"]
        tp = active_order["tp"]
        price = active_order["price"]

        result = place_bracket_order(self.provider, symbol, volume, buy_or_sell, sl, tp, price)

        if result.retcode == self.provider.TRADE_RETCODE_DONE:
            print("Active order placed successfully !")
            active_order["ticket"] = result.order
            return result.order
        else:
            print("Failed to place market order:", result.comment)
            return None

    def __place_pending_order(self):
        pending_index = self.box["pending_index"]
        pending_order = self.pre_orders[pending_index]
        
        symbol = pending_order["symbol"]
        volume = pending_order["volume"]
        buy_or_sell = pending_order["buy_or_sell"]
        sl = pending_order["sl"]
        tp = pending_order["tp"]
        price = pending_order["price"]

        result = place_pend_order(self.provider, symbol, volume, buy_or_sell, sl, tp, price)

        if result.retcode == self.provider.TRADE_RETCODE_DONE:
            print("Pending order placed successfully !")
            pending_order["ticket"] = result.order
            return result.order
        else:
            print("Failed to place pending order:", result.comment)
            return None

    def __close_pending_order(self ):
        ticket = self.pre_orders[self.box["pending_index"]]["ticket"]
        result = close_position(self.provider, ticket)
        if result:
            print("Pending order closed successfully !")
        else:
            print("Failed to close pending order !")

