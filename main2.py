import MetaTrader5 as mt5
import datetime as dt
import pandas as pd
import pytz 
import time
import os

key = open("./key.txt","r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"


# establish MetaTrader 5 connection to a specified trading account
if mt5.initialize(path=path,login=int(key[0]), password=key[1], server=key[2]):
    print("connection established")
   
# extract historic data
def get_hist_data_by_date(symbol , timeFrame , timeTill=None , numCandles = 200):
    """
    Parametrs
    ---------
    symbol : Type str - e.g "EURUSD"
    timeFrame: Type str - e.g "TIMEFRAME_M15"
    timeTill: Type str - e.g "YYYY-MM-DD HH:MM:SS"
    numCandles: Type int - e.g - e.g 200

    Returns
    -------
    historical data dataframe
    
    """
    current_tz = pytz.timezone("Asia/Tehran") #change this based on your location
    eet_tz = pytz.timezone("Europe/Kyiv")
    required_tz = pytz.timezone("Etc/UTC")
    
    if timeTill == None:
        timeTill = current_tz.localize(dt.datetime.now()).replace(tzinfo=required_tz)
    else:
        timeTill = eet_tz.localize(dt.datetime.strptime(timeTill, "%Y-%m-%d %H:%M:%S")).replace(tzinfo=required_tz)

    hist_data = mt5.copy_rates_from(symbol , getattr(mt5 , timeFrame) , timeTill, numCandles )
    data_frame = pd.DataFrame(hist_data)
    data_frame.time = pd.to_datetime(data_frame.time , unit="s")
    data_frame.set_index("time" , inplace=True)
    
    return data_frame

# hist_data = get_hist_data_by_date("EURUSD", "TIMEFRAME_M15") #get data till current time
# index = hist_data.index
# hist_data2 = get_hist_data_by_date("EURUSD", "TIMEFRAME_M15", dt.datetime.strftime(index[1], "%Y-%m-%d %H:%M:%S")) #get data till a specified time

# print("=========================")
# print(hist_data) 
# print("=========================")


def get_hist_data_by_index(symbol, timeFrame, startPos=0, numCandles=2):
    """
    Parameters
    ----------
    symbol : TYPE str - e.g "USDCAD"
    timeFrame : TYPE str - e.g. "TIMEFRAME_M15"
    startPos : TYPE int -e.g. 0 means data till current time
    numCandles : TYPE int

    Returns
    -------
    historical data dataframe

    """
    
    
    hist_data = mt5.copy_rates_from_pos(symbol, getattr(mt5, timeFrame), startPos, numCandles)   
    hist_data_df = pd.DataFrame(hist_data) 
    hist_data_df.time = pd.to_datetime(hist_data_df.time, unit="s")
    hist_data_df.set_index("time", inplace=True)
    return hist_data_df

hist_data = get_hist_data_by_index("EURUSD", "TIMEFRAME_M15") #get data till current time
print("=========================")
print(hist_data) 
print("=========================")
