import time

import MetaTrader5 as mt5

from mt5API import (
    close_position,
    current_price,
    get_orders_df,
    get_position_df,
    get_symbol_pip_unit,
    place_bracket_order,
    place_pend_order,
)

key = open("./key.txt", "r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"


# establish MetaTrader 5 connection to a specified trading account
if mt5.initialize(path=path, login=int(key[0]), password=key[1], server=key[2]):
    print("connection established")

symbol = "EURUSD"
num_boxes = 1  # Define the number of boxes you want to manage
box = {
    "id": 1,
    "index": 1,
    "next_price": 0.0,
    "active_tp": 0.0,
    "active_sl": 0.0,
    "pending_tp": 0.0,
    "pending_sl": 0.0,
    "pending_ticket": None,
    "position_ticket": None,
    "done": False,
}


def truncate_float(float_number, decimal_places):
    multiplier = 10**decimal_places
    return int(float_number * multiplier) / multiplier


def calcute_tp(cp):
    tp_pip = get_symbol_pip_unit(mt5, symbol) * 10

    if (box["index"] % 2) == 0:
        return truncate_float(cp - tp_pip, 5)
    else:
        return truncate_float(cp + tp_pip, 5)


def calcute_sl(cp):
    sl_pip = get_symbol_pip_unit(mt5, symbol) * 2

    if (box["index"] % 2) == 0:
        return truncate_float(cp + sl_pip, 5)
    else:
        return truncate_float(cp - sl_pip, 5)


def calculate_vol():
    c = 1.3
    lot = 0.1
    n = box["index"] - 3
    if box["index"] < 4:
        return lot
    else:
        return pow(c, n) * lot


def calculate_current_price():
    if (box["index"] % 2) == 0:
        askOrBid = False
    else:
        askOrBid = True

    cp = current_price(mt5, symbol, askOrBid)
    return truncate_float(cp, 5)


def place_market_order():
    cp = calculate_current_price()
    sl = calcute_sl(cp)
    tp = calcute_tp(cp)
    vol = calculate_vol()
    buyOrSell = "Buy"

    result = place_bracket_order(mt5, symbol, vol, buyOrSell, sl, tp, cp)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        box["next_price"] = sl
        box["index"] += 1
        box["active_tp"] = tp
        box["active_sl"] = sl
        box["active_ticket"] = result.order
        print("Market order placed successfully")
        return result.order
    else:
        print("Failed to place market order:", result.comment)
        return None


def place_pending_order():
    cp = box["next_price"]
    tp = calcute_tp(cp)
    sl = calcute_sl(cp)
    vol = calculate_vol()
    if (box["index"] % 2) == 0:
        buyOrSell = "Sell"
    else:
        buyOrSell = "Buy"

    result = place_pend_order(mt5, symbol, vol, buyOrSell, sl, tp, cp)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        box["next_price"] = sl
        box["index"] += 1
        box["pending_tp"] = tp
        box["pending_sl"] = sl
        box["pending_ticket"] = result.order

        print("Pending order placed successfully")
        return result.order
    else:
        print("Faisled to place pending order:", result.comment)
        return None


def close_pending_order():
    result = close_position(mt5, box["pending_ticket"])
    if result:
        print("Pending order closed successfully")
    else:
        print("Failed to close pending order")


def check_pending_order_exist():
    # print("PENDING TICKET IS:")
    # print(box["pending_ticket"])
    # print("-------------------")

    return get_orders_df(mt5, box["pending_ticket"])


def check_active_order_exist():
    # print("ACTIVE TICKET IS:")
    # print(box["active_ticket"])
    # print("-------------------")

    return get_position_df(mt5, box["active_ticket"])


def update_state():
    box["active_tp"] = box["pending_tp"]
    box["active_sl"] = box["pending_sl"]
    box["active_ticket"] = box["pending_ticket"]


def reset_state():
    box["id"] = 1
    box["index"] = 1
    box["next_price"] = 0.0
    box["active_tp"] = 0.0
    box["active_sl"] = 0.0
    box["pending_tp"] = 0.0
    box["pending_ticket"] = None
    box["position_ticket"] = None
    box["done"] = False


for box_id in range(1, num_boxes + 1):
    reset_state()
    place_market_order()

    # Main loop for managing the box
    while not box["done"]:
        place_pending_order()
        # Monitor the market and manage orders
        while True:
            pend_order = check_pending_order_exist()
            active_order = check_active_order_exist()

            if pend_order and active_order:
                pass
            elif pend_order is False and active_order is True:
                print("SL TOUCHED")
                update_state()
                break
            elif pend_order is True and active_order is False:
                print("TP TOUCHED")
                close_pending_order()
                box["done"] = True
                break
            else:
                pass

            time.sleep(0.8)  # Delay to avoid consuming too much CPU


# Shutdown MetaTrader 5 connection
mt5.shutdown()
