import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from account_credentials import LOGIN, PASSWORD, SERVER
import plotly.express as px
import requests

def check_allowed_trading_hours():
    tick = mt5.symbol_info_tick(symbol)
    # check the last price value to determine if the market is closed or available
    if tick.time != 0:
        market_status = True
        #market open
    else:
        market_status = False
        #market close
    return market_status

def market_order(symbol, volume, order_type, deviation=0, magic=123999):

    order_type_dict = {
        'buy': mt5.ORDER_TYPE_BUY,
        'sell': mt5.ORDER_TYPE_SELL
    }

    price_dict = {
        'buy': mt5.symbol_info_tick(symbol).ask,
        'sell': mt5.symbol_info_tick(symbol).bid
    }

    if order_type == 'buy':
        sl = mt5.symbol_info_tick(symbol).ask - (sl_price_range + spread)
        tp = mt5.symbol_info_tick(symbol).ask + (tp_price_range + spread)
    
    if order_type == 'sell':
        sl = mt5.symbol_info_tick(symbol).bid + (sl_price_range + spread)
        tp = mt5.symbol_info_tick(symbol).bid - (tp_price_range + spread)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,  # FLOAT
        "type": order_type_dict[order_type],
        "price": price_dict[order_type],
        "sl": sl,  # FLOAT
        "tp": tp,  # FLOAT
        "deviation": deviation,  # INTERGER
        "magic": magic,  # INTERGER
        "comment": strategy_name,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    return(order_result)


def close_position(position, deviation=0, magic=123999):

    order_type_dict = {
        0: mt5.ORDER_TYPE_SELL,
        1: mt5.ORDER_TYPE_BUY
    }

    price_dict = {
        0: mt5.symbol_info_tick(symbol).bid,
        1: mt5.symbol_info_tick(symbol).ask
    }

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position['ticket'],  # select the position you want to close
        "symbol": symbol,
        "volume": volume,  # FLOAT
        "type": order_type_dict[position['type']],
        "price": price_dict[position['type']],
        "deviation": deviation,  # INTERGER
        "magic": magic,  # INTERGER
        "comment": strategy_name,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    return(order_result)

def close_positions(order_type):
    order_type_dict = {
        'buy': 0,
        'sell': 1
    }

    if mt5.positions_total() > 0:
        positions = mt5.positions_get()

        positions_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())

        if order_type != 'all':
            positions_df = positions_df[(positions_df['type'] == order_type_dict[order_type])]

        for i, position in positions_df.iterrows():
            order_result = close_position(position)

            print('order_result: ', order_result)


symbol = 'XAUUSD'
timeframe = mt5.TIMEFRAME_H1
volume = 0.01
strategy_name = 'ML_lsvm'
sl_price_range = 3
tp_price_range = 3
spread = .125
deviation_delayed_trade = 0.300 #abs(current close price - previous complete close price) for example |1900.000 -1901.111| = 1.111
num_positions_max = 5

if __name__ == '__main__':
    is_initialized = mt5.initialize()
    print('initialize: ', is_initialized)

    is_logged_in = mt5.login(LOGIN, PASSWORD, SERVER)
    print('logged in: ', is_logged_in)
    print('\n')

#### RUN ONCE TO CREATE A RECORD.CSV FILE
try:
    time_records = pd.read_csv('time_records.csv')
    print('Your already have a time_records file: CONTINUE')
except:
    price_data = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)[0]
    open_price = price_data[1]
    high_price = price_data[2]
    low_price = price_data[3]
    close_price = price_data[4]
    time_trade = datetime.fromtimestamp(price_data[0])

    time_records = [time_trade]
    records_df = pd.DataFrame({'time_records': time_records})
    records_df.to_csv('time_records.csv', index=False)
    print('Created a time_records file')

time.sleep(2) # wait for server to start

while True:
    account_info = mt5.account_info()
    print(datetime.now(),
            '| Login: ', account_info.login,
            '| Balance: ', account_info.balance,
            '| Equity: ' , account_info.equity)
    num_positions = mt5.positions_total()
    print()
    print('Current Number of Positions: {0} (max:{1})'.format(num_positions,num_positions_max))

    if check_allowed_trading_hours() == False:
        if num_positions > 0:
            close_position('all')
            print('Closed all position')

    elif check_allowed_trading_hours() == True:
        # get the latest completed bar ( position [0])
        price_data = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)[0] 
        current_candle = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)[1]
        open = price_data[1]
        high = price_data[2]
        low = price_data[3]
        close = price_data[4] #This is all bid price on both completed and current candlestick
        time_trade = datetime.fromtimestamp(price_data[0])
        print("Complete candle >> Time: {0}, Open: {1}, High: {2}, Low: {3}, Close: {4}".format(time_trade,price_data[1],price_data[2],price_data[3],price_data[4]))
        print("Current candle >> Time: {0}, Open: {1}, High: {2}, Low: {3}, Close: {4}".format(datetime.fromtimestamp(current_candle[0]),current_candle[1],current_candle[2],current_candle[3],current_candle[4]))

        # Adjust time_trade format
        time_trade_str = time_trade.strftime('%Y-%m-%d %H:%M:%S')
        time_trade_ts = pd.Timestamp(time_trade_str)
        rounded_time_trade = time_trade_ts.floor('H')
        # Adjust imported time_records format
        time_records['time_records'] = pd.to_datetime(time_records['time_records'], format='%Y-%m-%d %H:%M:%S')
        rounded_time_records = time_records['time_records'].dt.floor('H')

        # temp check
        if rounded_time_trade not in rounded_time_records.values:
            print("It's not in  SO LET TRADE")
            print(rounded_time_trade)
        else:
            print("It's in the recorded")
            print(rounded_time_trade)

        ### Model LSVM BUY----------------------------------------------------------------
        if (rounded_time_trade not in rounded_time_records.values) and (num_positions <= 5):
            url = "http://127.0.0.1:5000/predict_api"

            data = {
                "data": {
                    "open": open,
                    "high": high,
                    "low": low,
                    "close": close
                }
            }
            try:
                response = requests.post(url, json=data)
            except:
                print("Cannot Reach ML Server, Aborting the bot")
                break

            if response.status_code == 200:
                prediction = response.json()
                print('prediction: ', prediction)
                
            else:
                print("POST request failed!")
                print(response.status_code)

            if prediction == 1:
                if abs(price_data[4] - current_candle[4]) > deviation_delayed_trade:
                    print("Deviation = {0} >>> No Trade, close price is out of deviation, wait for completed candle in the next hour".format((price_data[4] - current_candle[4])))
                elif abs(price_data[4] - current_candle[4]) <= deviation_delayed_trade:
                    order_result = market_order(symbol, volume, 'buy')
                    if order_result.retcode == mt5.TRADE_RETCODE_DONE: # check if trading order is successful
                        print("Deviation = {0} >>> Made a trade at: {1}".format((price_data[4] - current_candle[4]), time_trade))
                        new_row = pd.DataFrame({'time_records':[time_trade]})
                        time_records = pd.concat([time_records, new_row], axis=0) # love .append T.T
                        time_records.to_csv('time_records.csv') # record traded order by timestamp
                        #HW RECORD OPEN HIGH LOW CLOSE, PREDICTION TO CS
                    else:
                        "Sending order is not successful"
            
            if prediction == 0:
                #HW RECORD OPEN HIGH LOW CLOSE, PREDICTION TO CSV
                pass
            ### ---------------------------------------------------------------------------------

            ###HW Model LSVM BUY & SELL ----------------------------------------------------------------
            ### ---------------------------------------------------------------------------------


        ###HW ใส่ elif ว่า record แล้ว( if in time_records) แล้ว len ดู ข้อมูลตัวสุดท้ายใน df ว่า prediction เป็นเท่าไร แบบว่า ชั่วโมงนี้ predict ไปแล้วนะเว้ย ซึง เท่ากับ 1 หรือ 0 ก็ว่าไป
            #CODE HERE

        time.sleep(1)
    else:
        raise ValueError('Failed on Checking market status')
