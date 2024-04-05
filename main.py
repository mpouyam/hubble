import MetaTrader5 as mt5
import time

key = open("./key.txt","r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"


# establish MetaTrader 5 connection to a specified trading account
if mt5.initialize(path=path,login=int(key[0]), password=key[1], server=key[2]):
    print("connection established")

def current_price(symbol):
    si=mt5.symbol_info_tick(symbol) 
    return si.ask
    # return (si.bid + si.ask) / 2


def calcute_tp(box , cp ):
     tp_pip = 0.0010
     if (box % 2) == 0: return cp - tp_pip
     else: return cp + tp_pip

def calcute_sl(box , cp):
     sl_pip = 0.0002
     if (box % 2) == 0: return cp + sl_pip
     else: return cp - sl_pip

def calculate_vol(box):
    c = 1.3
    n = box - 3
    if box < 4 : return 0.1
    else: return pow(c, n) * 0.1

symbol = "EURUSD"
box = 1
cp = current_price(symbol)
tp = calcute_tp(box , cp)
sl = calcute_sl(box , cp)
vol = calculate_vol(box)

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": vol,
    "type": mt5.ORDER_TYPE_BUY,
    "price": cp,
    "sl": sl,
    "tp": tp,
    "deviation": 20,
    "magic": 234000,
    "comment": "python script open",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_RETURN,
}

# point=mt5.symbol_info(symbol).point
# request = {
#     "volume": 1.0,
#     "type": mt5.ORDER_TYPE_BUY,
#     "price": mt5.symbol_info_tick(symbol).ask,
#     "sl": mt5.symbol_info_tick(symbol).ask-100*point,
#     "tp": mt5.symbol_info_tick(symbol).ask+100*point,
#     "deviation": 10,
#     "magic": 234000,
#     "comment": "python script",
#     "type_time": mt5.ORDER_TIME_GTC,
#     "type_filling": mt5.ORDER_FILLING_RETURN,
# }
 
# send a trading request
result = mt5.order_send(request)

# check the execution result
print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,0.1,0.123,20));
if result.retcode != mt5.TRADE_RETCODE_DONE:
    print("2. order_send failed, retcode={}".format(result.retcode))
    # request the result as a dictionary and display it element by element
    result_dict=result._asdict()
    for field in result_dict.keys():
        print("   {}={}".format(field,result_dict[field]))
        # if this is a trading request structure, display it element by element as well
        if field=="request":
            traderequest_dict=result_dict[field]._asdict()
            for tradereq_filed in traderequest_dict:
                print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
    print("shutdown() and quit")
    mt5.shutdown()
    quit()
else : 
    print("00000000000000000")
    

history = mt5.orders_get()
print("=========================")
print(result)
print("=========================")
