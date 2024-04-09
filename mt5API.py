import datetime as dt

import pandas as pd
import pytz


# extract historic data
def get_hist_data_by_date(mt5, symbol, timeFrame, timeTill=None, numCandles=200):
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
    current_tz = pytz.timezone("Asia/Tehran")  # change this based on your location
    eet_tz = pytz.timezone("Europe/Kyiv")
    required_tz = pytz.timezone("Etc/UTC")

    if timeTill == None:
        timeTill = current_tz.localize(dt.datetime.now()).replace(tzinfo=required_tz)
    else:
        timeTill = eet_tz.localize(
            dt.datetime.strptime(timeTill, "%Y-%m-%d %H:%M:%S")
        ).replace(tzinfo=required_tz)

    hist_data = mt5.copy_rates_from(
        symbol, getattr(mt5, timeFrame), timeTill, numCandles
    )
    data_frame = pd.DataFrame(hist_data)
    data_frame.time = pd.to_datetime(data_frame.time, unit="s")
    data_frame.set_index("time", inplace=True)

    return data_frame


# hist_data = get_hist_data_by_date("EURUSD", "TIMEFRAME_M15") #get data till current time
# index = hist_data.index
# hist_data2 = get_hist_data_by_date("EURUSD", "TIMEFRAME_M15", dt.datetime.strftime(index[1], "%Y-%m-%d %H:%M:%S")) #get data till a specified time


def get_hist_data_by_index(mt5, symbol, timeFrame, startPos=0, numCandles=2):
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

    hist_data = mt5.copy_rates_from_pos(
        symbol, getattr(mt5, timeFrame), startPos, numCandles
    )
    hist_data_df = pd.DataFrame(hist_data)
    hist_data_df.time = pd.to_datetime(hist_data_df.time, unit="s")
    hist_data_df.set_index("time", inplace=True)
    return hist_data_df


# hist_data = get_hist_data_by_index("EURUSD", "TIMEFRAME_M15") #get data till current time


def place_market_order(mt5, symbol, vol, buyOrSell):
    if buyOrSell.capitalize()[0] == "B":
        direcetion = mt5.ORDER_TYPE_BUY
    else:
        direcetion = mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": vol,
        "price": mt5.symbol_info_tick(symbol).ask,
        "type": direcetion,
        "type_time": mt5.ORDER_TIME_GTC,
        # ORDER_TIME_GTC: The order stays in the queue until it is manually canceled
        # ORDER_TIME_DAY: The order is active only during the current trading day
        # ORDER_TIME_SPECIFIED: The order is active until the specified date
        # ORDER_TIME_SPECIFIED_DAY: The order is active until 23:59:59 of the specified day. If this time appears to be out of a trading session, the expiration is processed at the nearest trading time.
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    order_status = mt5.order_send(request)
    return order_status


def place_limit_order(mt5, symbol, vol, buyOrSell, pips_away):
    pip_unit = mt5.symbol_info(symbol).point * 10

    if buyOrSell.capitalize()[0] == "B":
        direcetion = mt5.ORDER_TYPE_BUY_LIMIT
        price = mt5.symbol_info_tick(symbol).ask - pips_away * pip_unit
    else:
        direcetion = mt5.ORDER_TYPE_SELL_LIMIT
        price = mt5.symbol_info_tick(symbol).bid + pips_away * pip_unit

    price = mt5.symbol_info(symbol).point * 10
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": vol,
        "price": price,
        "type": direcetion,
        "type_time": mt5.ORDER_TIME_GTC,
        # ORDER_TIME_GTC: The order stays in the queue until it is manually canceled
        # ORDER_TIME_DAY: The order is active only during the current trading day
        # ORDER_TIME_SPECIFIED: The order is active until the specified date
        # ORDER_TIME_SPECIFIED_DAY: The order is active until 23:59:59 of the specified day. If this time appears to be out of a trading session, the expiration is processed at the nearest trading time.
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    order_status = mt5.order_send(request)
    return order_status


# order with SL and TP
def place_bracket_order(mt5, symbol, vol, buy_sell, sl_price, tp_price):
    if buy_sell.capitalize()[0] == "B":
        direction = mt5.ORDER_TYPE_BUY
        price = current_price(mt5, symbol)

    else:
        direction = mt5.ORDER_TYPE_SELL
        price = current_price(mt5, symbol, ask=False)

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

    result = mt5.order_send(request)
    return result


def place_bracket_order_pip(mt5, symbol, vol, buy_sell, sl_pip, tp_pip):
    pip_unit = 10 * mt5.symbol_info(symbol).point
    if buy_sell.capitalize()[0] == "B":
        direction = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        sl = price - sl_pip * pip_unit
        tp = price + tp_pip * pip_unit

    else:
        direction = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        sl = price + sl_pip * pip_unit
        tp = price - tp_pip * pip_unit

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": vol,
        "type": direction,
        "sl": sl,
        "tp": tp,
        "price": price,
        "type_time": mt5.ORDER_TIME_GTC,
    }

    result = mt5.order_send(request)
    return result


def close_position(mt5, symbol, ticket: None):
    if ticket is None:
        mt5.Close(symbol, ticket)
    else:
        mt5.Close(symbol)


# place_bracket_order("USDCAD", 1.0, "buy", 1.3317, 1.3347)
# place_bracket_order_pip("GBPUSD", 1.0, "sell", 20, 40)
# order_res = limit_order("EURUSD", 0.03,   "buy", 6)


def get_position_df(mt5, symbol=None, ticket=None):
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    elif ticket:
        positions = mt5.positions_get(ticket=ticket)
    else:
        positions = mt5.positions_get()

    if len(positions) > 0:
        pos_df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        pos_df.time = pd.to_datetime(pos_df.time, unit="s")
        pos_df.drop(
            ["time_update", "time_msc", "time_update_msc", "external_id"],
            axis=1,
            inplace=True,
        )
    else:
        pos_df = pd.DataFrame()

    return pos_df


def get_orders_df(mt5, symbol=None, ticket=None):
    if symbol:
        orders = mt5.orders_get(symbol=symbol)
    elif ticket:
        orders = mt5.orders_get(ticket=ticket)
    else:
        orders = mt5.orders_get()

    if len(orders) > 0:
        ord_df = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
        ord_df.time_setup = pd.to_datetime(ord_df.time_setup, unit="s")
        # ord_df.drop(['time_update_msc'], axis=1, inplace=True)
    else:
        ord_df = pd.DataFrame()

    return ord_df


def current_price(mt5, symbol, ask=True):
    si = mt5.symbol_info_tick(symbol)
    if ask:
        return si.ask
    else:
        return si.bid


def get_symbol_pip_unit(mt5, symbol):
    si = mt5.symbol_info(symbol)
    return si.point * 10
