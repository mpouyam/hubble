import MetaTrader5 as mt5
import pandas as pd

# Connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()
    quit()

# Define the symbol and timeframe
symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_M1

# Retrieve historical candle data
candles = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)  # Get 100 last candles
df = pd.DataFrame(candles)
df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime

# Calculate moving averages
df['ma_10'] = df['close'].rolling(window=10).mean()
df['ma_30'] = df['close'].rolling(window=30).mean()

# Find cross
cross = False
if df['ma_10'].iloc[-2] < df['ma_30'].iloc[-2] and df['ma_10'].iloc[-1] > df['ma_30'].iloc[-1]:
    cross = True
elif df['ma_10'].iloc[-2] > df['ma_30'].iloc[-2] and df['ma_10'].iloc[-1] < df['ma_30'].iloc[-1]:
    cross = True

# Implement trading logic based on cross
if cross:
    # Execute your trading action here
    print("Cross detected! Implement your trading action here.")

# Disconnect from MetaTrader 5
mt5.shutdown()
