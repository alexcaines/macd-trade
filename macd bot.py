import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

# SOCKET = "wss://stream.binance.com:9443/ws/<symbol>@kline_<interval>" this is the format for diff tickers and intervals
SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_30m"

API_KEY = "uQ4ipme3gSMRtJ2URIoYx6nus9tWBtwld3ABYNQeoxbh2aBOUyTx62uMfyAli8nr"
API_SECRET = "ZAxvPSuA6XpUcrEjWVekbGjie5B78oqshJHQuX6NGHLpwJ42btyXH6ioRpnza6Ng"
client = Client(API_KEY, API_SECRET, tld='us')

MACD_PERIOD = 26
TRADE_SYMBOL = 'ETHUSD'
TRADE_QUANTITY = 0.005

closes = []
in_position = False

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes

    print('received message')
    json_message = json.loads(message)
    #pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("closes")
        print(closes)
        
        if len(closes) > MACD_PERIOD:
            np_closes = numpy.array(closes)
            real = EMA(np_closes, timeperiod = 200)
            macd, macdsig, macdhist = talib.MACD(np_closes, fastperiod=12, slowperiod=26, signalperiod=9)
            print("all macd's calculated so far")
            print(macd)
            last_ema = real[-1]
            last_macd = macd[-1]
            last_macdsig = macd_sig[-1]
            print("the current macd is {}".format(last_macd))
            
            if last_macd[-1] > 0 and last_ema > np_closes[-1] and last_macd[-2] > last_macdsig[-2] and last_macd[-1] < last_macdsig[-1]:
                if in_position:
                    print("sell xx")
                    #binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("bullish crossover but no position to close")
                 
                
            if last_macd[-1] < 0 and last_ema < np_closes[-1] and last_macd[-2] < last_macdsig[-2] and last_macd[-1] > last_macdsig[-1]:
                if in_position:
                    print("bullish crossover but already in a position")
                else:
                    print("buy xx")
                    # binance order logic/syntax
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()