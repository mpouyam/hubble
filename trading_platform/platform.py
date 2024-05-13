
import MetaTrader5 as mt5

class PlatformConfig: 
    def __init__(self, config_dict: dict = None) -> None:
        if config_dict is not None:
            self.path = config_dict.get('path')
            self.server = config_dict.get('server')
            self.login = config_dict.get('login')
            self.password = config_dict.get('password')
            self.symbol = config_dict.get('symbol')

    def set_path(self, path):
        self.path = path
        return self
    def get_path(self):
        return self.path
    
    def set_server(self, server):
        self.server = server
        return self
    def get_server(self):
        return self.server

    def set_login(self, login):
        self.login = login
        return self
    def get_login(self):
        return self.login

    def set_password(self, password):
        self.password = password
        return self
    def get_password(self):
        return self.password
    
    def set_symbol(self, symbol):
        self.symbol = symbol
        return self

    def get_symbol(self):
        return self.symbol


    def get_config(self) -> dict:
        return {
            'path': self.get_path(),
            'server': self.get_server(),
            'login': self.get_login(),
            'password': self.get_password(),
            'symbol': self.get_symbol()
        }
    

## Singleton
class Platform:
    def __init__(self) -> None:
        pass

    def get_instance(self):
        if not hasattr(self, 'instance'):
            self.instance = Platform()
        return self.instance
    
    def initialize(self, platform_config: PlatformConfig):
        self.platform_config = platform_config
        if mt5.initialize(
            path= "C:\\Program Files\\MetaTrader 5\\terminal64.exe", #platform_config.get_path(),
            login= platform_config.get_login(),
            password= platform_config.get_password(),
            server= platform_config.get_server(),
        ):
            print("Platform Initialized Successfuly.")
            return self
        else:
            raise Exception("Platform Initialization Failed!")
    

    
    def get_symbol_info(self, symbol: str):
        tick_info = mt5.symbol_info_tick(symbol)
        return (tick_info.time , tick_info.bid , tick_info.ask , tick_info.volume)
    
    def close_position(self, ticket):
        req = {"action": mt5.TRADE_ACTION_REMOVE, "order": ticket}
        result = mt5.order_send(req)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done" :True,
                "ticket": result.order,
                "comment": "Done"
            }
        else:
            return {
                "done" :False,
                "ticket": None,
                "comment": result.comment
            }


    def current_price(self, symbol, buy_sell):
        si = mt5.symbol_info_tick(symbol)
        if buy_sell == "BUY":
            return si.ask
        else:
            return si.bid

    def get_symbol_pip_unit(self, symbol):
        si = mt5.symbol_info(symbol)
        return si.point * 10

    def place_bracket_order(self, symbol, vol, buy_sell, sl_price, tp_price, price):        
        """
        Place a bracket order with MetaTrader 5.

        Args:
            symbol (str): The trading symbol (e.g., 'EURUSD').
            volume (float): The volume of the order.
            order_type (OrderType): The type of the order, either BUY or SELL.
            stop_loss_price (float): The price to set as the stop loss.
            take_profit_price (float): The price to set as the take profit.
            entry_price (float): The entry price for the order.

        Returns:
            dict: Result of the order operation including status and any relevant messages.
        """

        direction = mt5.ORDER_TYPE_BUY if buy_sell.startswith("B") else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": direction,
            "sl": sl_price,
            "tp": tp_price,
            "price": price,
            "type_time": mt5.ORDER_TIME_GTC,
        }


        result= mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done" :True,
                "ticket": result.order,
                "comment": "Done"
            }
        else:
            return {
                "done" :False,
                "ticket": None,
                "comment": result.comment
            }


    def place_pend_order(self, symbol, vol, buy_sell, sl, tp, cp):
        direction = mt5.ORDER_TYPE_BUY_STOP if buy_sell.startswith("B") else mt5.ORDER_TYPE_SELL_STOP

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": vol,
            "price": cp,
            "sl": sl,
            "tp": tp,
            "type": direction,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "done" :True,
                "ticket": result.order,
                "comment": "Done"
            }
        else:
            return {
                "done" :False,
                "ticket": None,
                "comment": result.comment
            }

