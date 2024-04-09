import MetaTrader5 as mt5

from mt5API import current_price, get_symbol_pip_unit, place_bracket_order

key = open("./key.txt", "r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"


# establish MetaTrader 5 connection to a specified trading account
if mt5.initialize(path=path, login=int(key[0]), password=key[1], server=key[2]):
    print("connection established")


def calcute_tp(symbol, order_index, cp):
    tp_pip = get_symbol_pip_unit(mt5, symbol) * 10
    if (order_index % 2) == 0:
        return cp - tp_pip
    else:
        return cp + tp_pip


def calcute_sl(symbol, order_index, cp):
    sl_pip = get_symbol_pip_unit(mt5, symbol) * 2
    if (order_index % 2) == 0:
        return cp + sl_pip
    else:
        return cp - sl_pip


def calculate_vol(order_index):
    c = 1.3
    n = order_index - 3
    if order_index < 4:
        return 0.1
    else:
        return pow(c, n) * 0.1


symbol = "EURUSD"
box = {"id": 1, "index": 2}
cp = current_price(mt5, symbol)
tp = calcute_tp(symbol, box["index"], cp)
sl = calcute_sl(symbol, box["index"], cp)
vol = calculate_vol(box["index"])

# request1 = {
#     "action": mt5.TRADE_ACTION_DEAL,
#     "symbol": symbol,
#     "volume": vol,
#     "type": mt5.ORDER_TYPE_BUY,
#     "price": cp,
#     "sl": sl,
#     "tp": tp,
#     "deviation": 20,
#     "magic": box["id"],
#     "type_time": mt5.ORDER_TIME_GTC,
#     "type_filling": mt5.ORDER_FILLING_RETURN,
# }

# send a trading request
# result = place_bracket_order(mt5, symbol, vol, "sell", sl, tp)


# # check the execution result
# print(
#     "1. order_send(): by {} {} lots at {} with deviation={} points".format(
#         symbol, 0.1, 0.123, 20
#     )
# )
# if result.retcode != mt5.TRADE_RETCODE_DONE:
#     print("2. order_send failed, retcode={}".format(result.retcode))
#     # request the result as a dictionary and display it element by element
#     result_dict = result._asdict()
#     for field in result_dict.keys():
#         print("   {}={}".format(field, result_dict[field]))
#         # if this is a trading request structure, display it element by element as well
#         if field == "request":
#             traderequest_dict = result_dict[field]._asdict()
#             for tradereq_filed in traderequest_dict:
#                 print(
#                     "       traderequest: {}={}".format(
#                         tradereq_filed, traderequest_dict[tradereq_filed]
#                     )
#                 )
#     print("shutdown() and quit")
#     mt5.shutdown()
#     quit()
# else:
#     print("00000000000000000")


# symbol = "EURUSD"
# box = {"id": 1, "index": 2}
# cp = current_price(mt5, symbol)
# tp = calcute_tp(symbol, box["index"], cp)
# sl = calcute_sl(symbol, box["index"], cp)
# vol = calculate_vol(box["index"])

# request2 = {
#     "action": mt5.TRADE_ACTION_DEAL,
#     "symbol": symbol,
#     "volume": vol,
#     "type": mt5.ORDER_TYPE_BUY,
#     "price": cp,
#     "sl": sl,
#     "tp": tp,
#     "deviation": 20,
#     "magic": box["id"],
#     "type_time": mt5.ORDER_TIME_GTC,
#     "type_filling": mt5.ORDER_FILLING_RETURN,
# }

# # send a trading request
# result = mt5.order_send(request2)


history = mt5.orders_get()
print("=========================")
print(history)
print("=========================")
