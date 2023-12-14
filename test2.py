# Kiteconnect Login
from kiteconnect import KiteConnect
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import talib

cwd = os.chdir("C:/Users/LENOVO/Documents/work/zerodha")

access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


scrips = ['RELIANCE','BAJFINANCE','ASIANPAINT','DIVISLAB','AXISBANK','M&M','TATASTEEL','TITAN','HCLTECH','BPCL','LICHSGFIN','TVSMOTOR','KOTAKBANK','EICHERMOT','SUNPHARMA','MUTHOOTFIN','MCDOWELL-N']

capital = 5000
buy_list = []
sell_list = []

current_time = time.strftime("%H:%M", time.localtime())

while current_time < '14:30':
    for scrip in scrips:
        
        last_candle = 2 # Choose the Last Candle
    
        # Get OHLC Data
        intraday_past_days = 5
        intraday_time_frame = '15minute'
        to_date = datetime.now()
        from_date = to_date - timedelta(days=int(intraday_past_days))
        scrip_data = kite.quote('NSE:'+scrip)
        scrip_token = scrip_data.get(('NSE:'+scrip),{}).get('instrument_token')
        intraday_data = kite.historical_data(scrip_token, from_date, to_date, intraday_time_frame)
        df_intraday = pd.DataFrame(intraday_data)
        df_intraday.columns =['Date & Time', 'Open','High','Low','Close','Volume']
        df_intraday = df_intraday[(df_intraday.Volume > 0)]
        #print(df_intraday)
        
        # Indicators
        df_intraday['ADX'] = talib.ADX(df_intraday['High'],df_intraday['Low'],df_intraday['Close'], timeperiod=14)
        df_intraday['RSI'] = talib.RSI(df_intraday['Close'], timeperiod=14)
        df_intraday['DOJI'] = talib.CDLDOJI(df_intraday['Open'],df_intraday['High'],df_intraday['Low'],df_intraday['Close'])
        df_intraday['DOJI'].replace(100,'Doji',inplace=True)
        df_intraday['MARUBOZU'] = talib.CDLCLOSINGMARUBOZU(df_intraday['Open'],df_intraday['High'],df_intraday['Low'],df_intraday['Close'])
        df_intraday['MARUBOZU'].replace(100,'Bullish Marubozu',inplace=True)
        df_intraday['MARUBOZU'].replace(-100,'Bearish Marubozu',inplace=True)
        df_intraday['HAMMER'] = talib.CDLHAMMER(df_intraday['Open'],df_intraday['High'],df_intraday['Low'],df_intraday['Close'])
        df_intraday['HAMMER'].replace(100,'Hammer',inplace=True)
        df_intraday['INVERTEDHAMMER'] = talib.CDLINVERTEDHAMMER(df_intraday['Open'],df_intraday['High'],df_intraday['Low'],df_intraday['Close'])
        df_intraday['INVERTEDHAMMER'].replace(100,'Inverted Hammer',inplace=True)
        df_intraday['HARAMICROSS'] = talib.CDLHARAMICROSS(df_intraday['Open'],df_intraday['High'],df_intraday['Low'],df_intraday['Close'])
        df_intraday['HARAMICROSS'].replace(100,'Bullish Harami',inplace=True)
        df_intraday['HARAMICROSS'].replace(-100,'Bearish Harami',inplace=True)
        df_intraday.replace(0,np.nan, inplace = True)
        df_intraday['Candle_Type'] = df_intraday[df_intraday.columns[7:]].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis = 1)
        df_intraday = df_intraday[['Date & Time', 'Open','High','Low','Close','Volume','RSI','Candle_Type','ADX']]
        # Logic for Buy/Sell
        
        rsi = df_intraday['RSI'].iloc[-last_candle]
        adx = df_intraday['ADX'].iloc[-last_candle]
        candle = df_intraday['Candle_Type'].iloc[-last_candle]
        date_time = df_intraday['Date & Time'].iloc[-last_candle]
        last_price = df_intraday['Close'].iloc[-last_candle]
        quant = int(capital/last_price)
        sl_buy_price = int(last_price - 0.00375 * last_price)
        sl_sell_price = int(last_price + 0.00375 * last_price)
        tgt_buy_price = int(last_price + 0.0085 * last_price)
        tgt_sell_price = int(last_price - 0.0085 * last_price)
        # print(scrip, rsi, candle)
        
        if rsi < 30 and adx < 55 and (scrip not in buy_list) and (candle == 'Doji' or candle =='Hammer' or candle =='Bullish Marubozu' or candle =='Bullish Harami'):
            print(date_time,'- Buy',scrip,'@',last_price)
            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='BUY',
                            quantity=quant,
                            order_type='LIMIT',
                            price = last_price,
                            product='MIS',
                            variety='regular')
            buy_list.append(scrip)
            
            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='SELL',
                            quantity=quant,
                            order_type='SL-M',
                            trigger_price = sl_buy_price,
                            product='MIS',
                            variety='regular')
            
            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='SELL',
                            quantity=quant,
                            order_type='LIMIT',
                            price = tgt_buy_price,
                            product='MIS',
                            variety='regular')
            
        if rsi > 70 and adx < 55 and (scrip not in sell_list) and (candle == 'Doji' or candle =='Inverted Hammer' or candle =='Bearish Marubozu' or candle =='Bearish Harami'):
            print(date_time,'- Sell',scrip,'@',last_price)
            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='SELL',
                            quantity=quant,
                            order_type='LIMIT',
                            price = last_price,
                            product='MIS',
                            variety='regular')
            sell_list.append(scrip)

            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='BUY',
                            quantity=quant,
                            order_type='SL-M',
                            trigger_price = sl_sell_price,
                            product='MIS',
                            variety='regular')
            
            kite.place_order(tradingsymbol=scrip,
                            exchange='NSE',
                            transaction_type='BUY',
                            quantity=quant,
                            order_type='LIMIT',
                            price = tgt_sell_price,
                            product='MIS',
                            variety='regular')
            
    current_time = time.strftime("%H:%M", time.localtime())
    
# Exit all at EOD
def placeMarketOrder(symbol,buy_sell,quantity):    
    # Place an intraday market order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
def CancelOrder(order_id):    
    # Modify order given order id
    kite.cancel_order(order_id=order_id,
                    variety=kite.VARIETY_REGULAR)
a,b = 0,0
while a < 10 and  current_time > '15:00':
    try:
        pos_df = pd.DataFrame(kite.positions()["day"])
        break
    except:
        print("can't extract position data..retrying")
        a+=1
while b < 10 :
    try:
        ord_df = pd.DataFrame(kite.orders())
        break
    except:
        print("can't extract order data..retrying")
        b+=1

#closing all open position   
for i in range(len(pos_df)):
   ticker = pos_df["tradingsymbol"].values[i]
   if pos_df["quantity"].values[i] > 0 :
        quantity = pos_df["quantity"].values[i]
        placeMarketOrder(ticker,"sell", quantity)
   if pos_df["quantity"].values[i] < 0 :
        quantity = abs(pos_df["quantity"].values[i])
        placeMarketOrder(ticker,"buy", quantity)

#closing all pending orders
pending = ord_df[ord_df['status'].isin(["TRIGGER PENDING","OPEN"])]["order_id"].tolist()
drop = []
attempt = 0
while len(pending)>0 and attempt<5 and time.time() > timeout:
    pending = [j for j in pending if j not in drop]
    for order in pending:
        try:
            CancelOrder(order)
            drop.append(order)
        except:
            print("unable to delete order id : ",order)
            attempt+=1                   
# =============================================================================

# Monitor Positions

