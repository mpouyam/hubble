from strategies import Trader
from repository import BoxRepositoryInterface
from utils import now_time_iran
from typing import Any, Dict


class TraderMock(Trader):
    def __init__(self , provider , logger , repository:BoxRepositoryInterface , symbol:str) -> None:
        super().__init__(provider , logger , repository, symbol)


    def on_tick(self, tick) -> None:
        self._box_state_manager(bid=tick[1], ask=tick[2])
        return

    def __is_working_hours(self) -> bool:
        return True

    # def _save_data(self) -> None:
    #     return
    
    # def _close_order(self) -> None:
    #     if self.active_order is None: return

    #     active_order_ticket = self.active_order["ticket"]

    #     result = self.provider.close_position(active_order_ticket , self.symbol)
    #     if result["done"]:
    #         self.active_order["state"] = "CLOSED"
    #         self.active_order["ended_at"] = now_time_iran()
    #         self.__add_to_orders(self.active_order)

    #     else:        
    #         self.active_order["state"] = "FAILED"
    #         self.active_order["error"] = result["comment"]
    #         self.__add_to_orders(self.active_order)
        
    #     return self.active_order

    # def _place_order(self , order_number: int ,spread:float):

    #     self._calculate_order(order_number)

    #     self.active_order["spread"] = spread

    #     symbol = self.active_order["symbol"]
    #     volume = self.active_order["volume"]
    #     buy_or_sell = self.active_order["buy_or_sell"]
    #     sl = self.active_order["sl"]
    #     tp = self.active_order["tp"]
    #     price = self.active_order["price"]

    #     result = self.provider.place_bracket_order(symbol, volume, buy_or_sell, sl, tp, price)
        
    #     if result["done"]:
    #         self.logger.info("Active order placed successfully !")
    #         self.active_order["ticket"] = result["ticket"]
    #         self.active_order["state"] = "ACTIVE"

    #     else:
    #         self.logger.error("Maximum retries reached for placing active order.")
    #         self.active_order["state"] = "FAILED"
    #         self.active_order["error"] = result["comment"]
    #         self.__add_to_orders(self.active_order)
            
    #     return self.active_order
    
    def _tp_action(self):
        # self._set_status("OFF")
        self._set_box_state("FINISHED")
        self._save_data()
        self._reset_order_state()
        self._reset_box_state()

    def _initialize_order_config(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "first_order_signal": "BUY",
            "pip_unit": self.provider.get_symbol_pip_unit(self.symbol),
            "try_count": 9,
            "tp_limit": 6,
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
