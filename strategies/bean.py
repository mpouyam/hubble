from mt5API import (
    close_position,
    current_price,
    get_symbol_pip_unit,
    place_bracket_order,
    place_pend_order,
)

class BeanStrategy:
    # constructor
    def __init__(self, provider, symbol) -> None:
        self.box = {
            "symbol": symbol,
            "active_index": 1,
            "pending_index": 2,
        }
        self.provider = provider
        self.pre_orders = [None]
        self.max_order = 30


    # strategy public method
    def start(self):
        self.__calculate_pre_orders()
        self.__place_active_order()
        self.__place_pending_order()
        print("New Box Is Starting :)")

    def on_tick(self , tick):
        self.__state_manager(tick)

    def get_symbol(self):
        return self.box["symbol"]


    # oder actions
    def __place_active_order(self):
        symbol = self.pre_orders[self.box["active_index"]]["symbol"]
        volume = self.pre_orders[self.box["active_index"]]["volume"]
        buyOrSell = self.pre_orders[self.box["active_index"]]["buyOrSell"]
        sl = self.pre_orders[self.box["active_index"]]["sl"]
        tp = self.pre_orders[self.box["active_index"]]["tp"]
        price = self.pre_orders[self.box["active_index"]]["price"]

        result = place_bracket_order( self.provider, symbol, volume, buyOrSell, sl, tp, price)

        if result.retcode == self.provider.TRADE_RETCODE_DONE:
            print("Market order placed successfully")
            self.pre_orders[self.box["active_index"]]["ticket"] = result.order
            return result.order
        else:
            print("Failed to place market order:", result.comment)
            return None

    def __place_pending_order(self):        
        symbol = self.pre_orders[self.box["pending_index"]]["symbol"]
        volume = self.pre_orders[self.box["pending_index"]]["volume"]
        buyOrSell = self.pre_orders[self.box["pending_index"]]["buyOrSell"]
        sl = self.pre_orders[self.box["pending_index"]]["sl"]
        tp = self.pre_orders[self.box["pending_index"]]["tp"]
        price = self.pre_orders[self.box["pending_index"]]["price"]

        result = place_pend_order(
            self.provider, symbol, volume, buyOrSell, sl, tp, price
        )

        if result.retcode == self.provider.TRADE_RETCODE_DONE:
            print("Pending order placed successfully")
            self.pre_orders[self.box["pending_index"]]["ticket"] = result.order
            return result.order
        else:
            print("Failed to place pending order:", result.comment)
            return None

    def __close_pending_order(self ):
        ticket = self.pre_orders[self.box["pending_index"]]["ticket"]
        result = close_position(self.provider, ticket)
        if result:
            print("Pending order closed successfully")
        else:
            print("Failed to close pending order")



    # manage state
    def __reset_state(self):
        self.pre_orders=[None]
        self.box["active_index"] = 1
        self.box["pending_index"] = 2
        print("This Box is Done and State is cleared")

    def __update_state(self):
        self.box["active_index"] += 1
        self.box["pending_index"] += 1

    def __state_manager(self , tick):
        active_order = self.pre_orders[self.box["active_index"]]
        active_sl = active_order["sl"]
        active_tp = active_order["tp"]
        active_direction = active_order["buyOrSell"]
        bid = tick[1]
        ask = tick[2]
        if active_direction == "BUY" :
            # if price touched our active order tp -> close pending position -> reset state -> start again
            if bid >= active_tp :
                self.__close_pending_order()
                self.__reset_state()
                self.start()
            
            # if price touched active order sl -> our pending order activate -> change box state -> place pendig order
            elif bid <= active_sl:
                self.__update_state()
                self.__place_pending_order()
            
            else:
                return
        else: 
            # if price touched our active order tp -> close pending position -> reset state -> start again
            if ask <= active_tp :
                self.__close_pending_order()
                self.__reset_state()
                self.start()
            
            # if price touched active order sl -> our pending order activate -> change box state -> place pendig order
            elif ask >= active_sl:
                self.__update_state()
                self.__place_pending_order()
            
            else:
                return

   
    #  Calculate Orders
    def __calculate_pre_orders(self):
        for i in range(1 , self.max_order + 1):
            buyOrSell = self.__buy_or_sell(i)
            vol = self.__calculate_vol(i)

            if i == 1 :
                cp = self.__calculate_current_price(buyOrSell)
                (tp , sl) = self.__calcute_tp_sl(cp, buyOrSell)

            elif  i == 2 :
                cp = self.pre_orders[1]["sl"]
                (tp , sl) = self.__calcute_tp_sl(cp, buyOrSell)

            else :
                if (i % 2)!=0 :
                    tp = self.pre_orders[1]["tp"]
                    sl = self.pre_orders[1]["sl"]
                    cp = self.pre_orders[1]["price"]
                else:
                    tp = self.pre_orders[2]["tp"]
                    sl = self.pre_orders[2]["sl"]
                    cp = self.pre_orders[2]["price"]



            request = {
                "index":i,
                "buyOrSell": buyOrSell,
                "ticket":None,
                "symbol": self.box["symbol"],
                "volume": vol,
                "sl": sl,
                "tp": tp,
                "price": cp,
            }

            self.pre_orders.append(request)
            
    def __buy_or_sell(self , index ):
        # we start with buy so odd numbers will be buy and even will be sell
        if (index% 2) == 0:
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

    def __calcute_tp_sl(self, cp , buyOrSell):
        pip_uint = get_symbol_pip_unit(self.provider, self.box["symbol"])

        tp_pip = pip_uint * 10
        sl_pip = pip_uint * 2
        
        if buyOrSell == "SELL":
            tp_price =cp - tp_pip
            sl_price = cp + sl_pip

        else:
            tp_price = cp + tp_pip
            sl_price = cp - sl_pip

        return (round(tp_price , 5), round(sl_price,5))

    def __calculate_current_price(self , buyOrSell):
        return current_price(self.provider, self.box["symbol"], buyOrSell)

