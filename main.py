import MetaTrader5 as mt5

from strategies import BeanStrategy

key = open("./key.txt", "r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# establish MetaTrader 5 connection to a specified trading account
if mt5.initialize(path=path, login=int(key[0]), password=key[1], server=key[2]):
    print("connection established")

symbol = "EURUSD"
bean = BeanStrategy(mt5 , symbol)
bean.start()


# Shutdown MetaTrader 5 connection
mt5.shutdown()
