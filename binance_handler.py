

api_key_ = "B9MMcfPN49IH8mlC8iAia8dW1HG6gQ5IXG8k4AIgYkX5nT01GVCQBiIZlhPiPbJ"
api_secret_ = "ig2b0FuLpU7Ts1VlgcqAjBMdF8D8cSlgXQD43Mdjdsoxtgoqo2gKi4JEapAioNi"

percentage_of_balance = 90 #%
leverage = 17
stop_loss =2 #%


import time
import json
from binance.client import Client, BinanceRequestException, BinanceAPIException, NotImplementedException
from binance.enums import ORDER_TYPE_LIMIT, FUTURE_ORDER_TYPE_LIMIT_MAKER,FUTURE_ORDER_TYPE_TAKE_PROFIT,FUTURE_ORDER_TYPE_STOP,ORDER_TYPE_STOP_LOSS, SIDE_BUY, SIDE_SELL, TIME_IN_FORCE_GTC,ORDER_TYPE_TAKE_PROFIT, ORDER_TYPE_MARKET,ORDER_TYPE_STOP_LOSS_LIMIT
import math
import pandas as pd
from datetime import datetime



leverage = 1
def write_logs(sentence):
    with open("logs.txt",'a') as fl :
        fl.write(str(datetime.now())+'::'+sentence+'\n')

def write_logs_close(sentence):
    with open("logs_closer.txt",'a') as fl :
        fl.write(sentence+'\n')


#write_logs(str(datetime.now())+" ::: Error: "+str(e))
class binance_handler:

    def __init__(self,api_key=api_key_, api_secret=api_secret_) :
        self.client =Client(api_key=api_key,api_secret=api_secret)
        self.symb ={}
        self.symp ={}
        inf = self.client.futures_exchange_info()
        p = inf['symbols']
        for i, elts in enumerate(p):
            auxs = elts['symbol']
            if auxs.endswith('USDT'):
                self.symb[auxs] = int(elts['quantityPrecision'])
                self.symp[auxs] = int(elts['pricePrecision'])
        self.symb['BTCUSDT'] = 3
        self.symp['BTCUSDT'] = 1
        print('logging to binance is successful! ')
        print("Ready to run !")

    def get_price(self,symbol):
        """
        Returns the price of the asset passed in the parameters
        """
        try:
            res = self.client.futures_mark_price(symbol=symbol)
            write_logs(str(datetime.now()) + " ::: Got price : " + str(res['markPrice']))
            return float(res['markPrice'])

        except Exception as e:
            write_logs(str(datetime.now()) + " ::: Error getting price : " + str(e))
            
    def change_leverage(self,ticker,leverage):
        try:
            self.client.futures_change_leverage(symbol=ticker,leverage=leverage)
        except Exception as e:
            print(e)
    

    def post_open_position(self,symbol,perc,side ='buy'):
        try:
            write_logs(str(datetime.now()) + " ::: Open order recieved for : " + symbol + " and side "+side )
            last =  self.get_price(symbol)
            write_logs(str(datetime.now()) + " :::              Price for  : " + symbol + " is " + str(last))
            balance = self.get_balance()
            write_logs(str(datetime.now()) + " :::              balance is  : " + str(balance) +" and percentage is "+ str(perc) )
            amount = balance*perc/100/last
            write_logs(str(datetime.now()) + " :::              resulting amount is  : " + str(amount) )
            print(f'   Balance {balance} Last price {last} quantity {amount}')
            #side_ = "sell" if side == 'buy' else 'buy'
            temp1 = self.check_open_position(ticker=symbol,side_new=side)

            if temp1:
                write_logs(str(datetime.now()) + " :::             Already in position : " + side)
            else:
                write_logs(str(datetime.now()) + " :::             changing leverage : " + side)
                self.change_leverage(symbol,leverage)
                write_logs(str(datetime.now()) + " :::             Not in position, placing order  : " + side + " Amount is  : " + str(amount))
                if side.lower() == 'buy':
                    #res = self.ftx.create_market_order(symbol=symbol,side=side,amount=amount*leverage)
                    res = self.place_market_long_order(symbol, amount,last)

                if side.lower() == 'sell':
                    #res = self.ftx.create_market_order(symbol=symbol,side=side,amount=amount*leverage)
                    res = self.place_market_short_order(symbol, amount,last)

                write_logs(
                    str(datetime.now()) + " :::             Placing stop loss  : " + side + " Amount is  : " + str(
                        amount))

                sl = last*(1-stop_loss/100) if side =='buy' else last*(1+stop_loss/100)
                side_sl = 'sell' if side =='buy' else 'buy'

                if side.lower() == 'buy':
                    res =self.place_sl_long_order(ticker=symbol, quantity=amount,price=sl)
                    write_logs(
                    str(datetime.now()) + " :::             placed stop loss long : " +  str( res))

                if side.lower() == 'sell':
                    res= self.place_sl_short_order(ticker=symbol, quantity=amount,price=sl)
                    write_logs(
                    str(datetime.now()) + " :::             placed stop loss  short : " +  str( res))
            
    
            return amount
        except Exception as e:
            print("Erorr in placing long: "+str(e))
            write_logs(  str(datetime.now()) + " :::             Error  : " + str(e))


    def get_balance(self):
        """
        Returns the available usdt balance
        """
        try:
            for position in self.client.futures_account_balance():
   
                if position['asset']=="USDT": 
                    write_logs(str(datetime.now()) + " ::: Balance : " + str(position['balance']))
                    return float(position['balance'])
        except Exception as e:
            print(e)
            write_logs(str(datetime.now()) + " ::: Error in balance fetching: " + str(e))
    
    def get_portfolio(self):
        """
        Returns the available usdt balance
        """
        try:
            total = 0
            tickss =  self.client.get_all_tickers()
            ticks = {}
            for elt in tickss:
                ticks[elt['symbol']] = float(elt['price'])
            

            for position in self.client.futures_account_balance():
                try:

                    if position['asset']=="USDT": 
                        total += float(position['balance'])
                        write_logs(str(datetime.now()) + " ::: Balance : " + str(position['balance']))
                        
                    else:
                        total +=  float(ticks[position['asset']+'USDT'])*float(position['balance'])
                except Exception as e:
                    print(e)
            print('Total :  ', total)
            return total

        except Exception as e:
            print(e)
            write_logs(str(datetime.now()) + " ::: Error in balance fetching: " + str(e))
            return 0

    def post_open_pos(self,symbol,amount,side ='buy'):
        
        try:
            write_logs(str(datetime.now()) + " ::: Open order recieved for : " + symbol + " and side "+side )
            last =  self.get_price(symbol)
            #write_logs(str(datetime.now()) + " :::              balance is  : " + str(balance) +" and percentage is "+ str(perc) )
            amount = amount/last*leverage
            write_logs(str(datetime.now()) + " :::              resulting amount is  : " + str(amount) )
            #print(f'   Balance {balance} Last price {last} quantity {amount}')
            #side_ = "sell" if side == 'buy' else 'buy'
           
           
            if side=="buy":
                res= self.place_market_long_order(symbol, amount)
                print( '   Order result = ',res)
                write_logs(str(datetime.now()) + " :::             Not in position, placing order  : " + side + " Amount is  : " + str(amount))
            
            if side=="sell":
                res= self.place_market_short_order(symbol, amount)
                write_logs(str(datetime.now()) + " :::             Not in position, placing order  : " + side + " Amount is  : " + str(amount))
   
            return amount
        except Exception as e:
            print("Erorr in placing long: "+str(e))
            write_logs(  str(datetime.now()) + " :::             Error  : " + str(e))

    def place_stop_limit_long_order(self,ticker, quantity,price):
        try:
            self.client.futures_change_margin_type(symbol=ticker, marginType='ISOLATED')
        except Exception as e:
            print(e)
        try:
            print('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),)
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_BUY,
            price='{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),
            stopPrice='{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),
            positionSide='LONG',
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=FUTURE_ORDER_TYPE_STOP ) 
            if order:
                print('Future Long order placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()]),'',order
        
        except Exception as e:
            print(e)
            print('Error in Longing Future '+ ticker+str(e))
            return False,'','',str(e),''

    def place_stop_limit_short_order(self,ticker, quantity,price):
        try:
            self.client.futures_change_margin_type(symbol=ticker, marginType='ISOLATED')
        except Exception as e:
            print(e)

        try:
 
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_SELL,
            price='{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),
            stopPrice='{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),
            positionSide='SHORT',
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=FUTURE_ORDER_TYPE_STOP ) 
              
            if order:
                print('Future short order placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()]),'',order
        
        except Exception as e:
            print(e)
            print('Error in shorting Future '+ ticker+str(e))
            return False,'','',str(e),''


    def place_market_long_order(self,ticker, quantity,price):
        #try:
        #    self.client.futures_change_margin_type(symbol=ticker, marginType='ISOLATED')
        #except Exception as e:
        #    print(e)
    
        try:
            #price='{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),
            #print('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),self.symp)
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_BUY,
            positionSide='LONG',
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=ORDER_TYPE_MARKET)
            if order:
                print('Future Long order market placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()]),'',order
        
        except Exception as e:
            print(e)
            print('Error in market Longing Future '+ ticker+str(e))
            return False,'','',str(e),''

    def place_tp_long_order(self,ticker, quantity,price):
    
        try:
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_SELL,
            price=('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            stopPrice =('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            positionSide='LONG',
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT)
            if order:
                print('Future tp long placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])
        
        except Exception as e:
            print(e)
            print('Error in tp long Future '+ ticker+str(e))
            return False,'',''
    
    def place_sl_long_order(self,ticker, quantity,price):
    
        try:
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_SELL,
            positionSide='LONG',
            stopPrice=('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type='STOP_MARKET')
            if order:
                print('Future sl long placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])
        
        except Exception as e:
            print(e)
            print('Error in sl sl long Future '+ ticker+str(e))
            return False,'',''
        
    def place_sl_short_order(self,ticker, quantity,price):
    
        try:
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_BUY,
            positionSide='SHORT',
            stopPrice=('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type="STOP_MARKET")
            if order:
                print('Future sl short placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])
        
        except Exception as e:
            print(e)
            print('Error in sl short Future '+ ticker+str(e))
            return False,'',''

    def check_order(self, symbol, order_id):
        try:
            temp = self.client.futures_get_order(symbol=symbol, orderId=int(order_id))
            if temp['status']== 'FILLED':
                return temp
            if temp['status'] == 'CANCELED':
                return ""
            return False
        except Exception as e:
            print(e)
            return ""

    def continous_order_check(self,symbol, order_id, times=10):
        for i in range(times):
            time.sleep(3)
            print(f"Continous check {i} out of {times}")
            chk = self.check_order( symbol, order_id)
            if chk!= False and chk != '':
                print(f'Limit  order filled for {symbol} ')
                return chk
            elif chk =='':
                print('   No order or order canceled')
                break
            else:
                print('   Order not filled yet')
        
        print(f'Limit  order not filled for {symbol}  Canceling it')
        self.client.cancel_order(symbol, order_id)
        return False

    def cancel_order_with_id(self, symbol,order_id):
        try:
            temp = self.client.futures_cancel_order(symbol = symbol, orderId= order_id)
            return True

        except Exception as e:
            print(e)
            if ' Unknown order sent.' in str(e):
                return  True
            return False


    def cancel_order(self, symbol):
        try:
            temp = self.client.futures_cancel_all_open_orders(symbol=symbol)
            return True

        except Exception as e:
            print(e)
            if ' Unknown order sent.' in str(e):
                return  True
            return False

    def place_market_short_order(self,ticker, quantity,price):
        try:
            self.client.futures_change_margin_type(symbol=ticker, marginType='ISOLATED')
        except Exception as e:
            print(e)
        try:
            #price=('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_SELL,
            positionSide='SHORT',
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=ORDER_TYPE_MARKET)
            if order:
                print('Future Market short order placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()]),'',order
        
        except Exception as e:
            print(e)
            print('Error in market shorting Future '+ ticker+str(e))
            return False,'','', str(e),''

    def close_position(self,symbol,qty, side='LONG'):
        long =qty
        short=qty
        sd= None
   
        if side == 'SHORT':
            sd = SIDE_BUY
            qty= short
        elif side == 'LONG':
            sd = SIDE_SELL
            qty= long
        try:
            print(f"Closing {symbol} {sd} {qty}  ")
            order = self.client.futures_create_order(
            symbol=symbol,
            side=sd,
            positionSide=side,
            quantity=('{:0.0{}f}'.format(qty, self.symb[symbol.strip().upper()])),
            type=ORDER_TYPE_MARKET
            )
            if order:
                print('Future Sell order placed for: '+symbol)
                print(order)
                return order['avgPrice']
        except Exception as e:
            print(e)
            write_logs(str(datetime.now()) + " :::     Error  in closing : " + str(e))
            return e
    
    def place_tp_short_order(self,ticker, quantity,price):
    
        try:
            order = self.client.futures_create_order(
            symbol=ticker,
            side=SIDE_BUY,
            price=('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            stopPrice =('{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()])),
            positionSide='SHORT',
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=('{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])),
            type=ORDER_TYPE_TAKE_PROFIT)
            if order:
                print('Future tp short placed for: '+ticker)
                return order['orderId'],'{:0.0{}f}'.format(price, self.symp[ticker.strip().upper()]),'{:0.0{}f}'.format(quantity, self.symb[ticker.strip().upper()])
        
        except Exception as e:
            print(e)
            print('Error in tp short Future '+ ticker+str(e))
            return False,'',''

    def get_and_close_open_position(self,ticker):
        try:
            temp = self.client.futures_position_information(symbol=ticker)
            no_position = True
            for elt in temp:
                if elt['symbol'] ==ticker and float(elt['positionAmt']) != 0:
                    side = 'LONG' if float(elt['positionAmt']) >0 else 'SHORT'
                    symbol = elt['symbol']
                    quantuty = abs(float(elt['positionAmt']))
                    print("Closing ", symbol,side,quantuty)
                    self.close_position(symbol=symbol,qty=quantuty,side=side)
                    return True
                    
            return no_position

        except Exception as e:
            print(e)
            if ' Unknown order sent.' in str(e):
                return  True
            return False

    def check_open_position(self,ticker,side_new=""):
        try:
            temp = self.client.futures_position_information(symbol=ticker)
       
            for elt in temp:
                if elt['symbol'] ==ticker and float(elt['positionAmt']) != 0:
                    side = 'LONG' if float(elt['positionAmt']) >0 else 'SHORT'
                    symbol = elt['symbol']
                    quantuty = abs(float(elt['positionAmt']))
                    print("Closing ", symbol,side,quantuty)
                    if side == side_new.upper():
                        return True
                    
            return False

        except Exception as e:
            print(e)
            if ' Unknown order sent.' in str(e):
                return  True
            return False



#m = binance_handler()


#print(m.get_and_close_open_position(ticker='BTCUSDT'))