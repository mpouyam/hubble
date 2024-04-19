class beanStrategy:
    def __init__(self, mt5) -> None:
        self.state = {
            "id": 1,
            "index": 1,
            "active_tp": 0.0,
            "active_sl": 0.0,
            "pending_tp": 0.0,
            "pending_sl": 0.0,
            "active_ticket ": None,
            "pending_ticket": None,
        }
        self.pre_orders = []
        self.__calculate_orders(self)
        self.provider = mt5

    def __calculate_orders(self, cb) -> None:
        self.pre_orders.insert(0, "apple")
        print(self.pre_orders)

    def calculate_vol(self):
        c = 1.3
        lot = 0.1
        n = self.state["index"] - 3
        if self.state["index"] < 4:
            return lot
        else:
            return pow(c, n) * lot

    def start():
        # place_bracket_order_pip
        #
        # place_pend_order
        # check price for getting price :
        # 1- if sl touched pending order activate automatically
        # 2- if tp touched close pending order
        # first box done
        # go for next box
        print("order placed")


beanStrategy()
