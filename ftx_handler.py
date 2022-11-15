

api_key = "bx6mXz8PJX443rhu4jeGMTpH3J8-7jWMYksTE8BT"
api_secret = "33ApHkWO4ovj9hOZzyNpygtHji8l3W45ar6WO_TN"
sub_account_name = "alpha1"
percentage_of_balance = 90 #%
leverage = 17
stop_loss =98 #%


import math
import ccxt
import pandas as pd
from datetime import datetime

def write_logs(sentence):
    with open("logs.txt",'a') as fl :
        fl.write(sentence+'\n')
#write_logs(str(datetime.now())+" ::: Error: "+str(e))
class ftx_handler:
    def __init__(self, unit='usdValue'):
        if sub_account_name !='':
            self.ftx = ccxt.ftx({
                'api_key': api_key,  # API Keys
                'secret': api_secret,
                'headers': {
                    'FTX-SUBACCOUNT': sub_account_name
                }
            })
        else:
            self.ftx = ccxt.ftx({
                'api_key': api_key,  # API Keys
                'secret': api_secret
            })
        self.unit = unit

    def get_balance(self):
        try:
            temp  = self.ftx.fetch_balance()
            print(temp)
            res = 0
            print(temp['info']['result'])
            for elt in temp['info']['result']:
                if elt['coin'] == 'ETH':
                    print(elt['usdValue'])
                    res += float(elt['usdValue'])
                if elt['coin'] == 'USD':
                    res += float(elt['total'])
            return res
        except Exception as e:
            write_logs(str(datetime.now()) + " ::: Error in balance fetching: " + str(e))

    def get_open_pos(self):
        #print(self.ftx.fetch_positions())
        try:
            temp = {"buy":{},"sell":{}}
            for elt in self.ftx.fetch_positions():
                if elt['info']['side'] =="buy":
                    temp["buy"][elt['info']['future']] = elt['info']['size']
                if elt['info']['side'] =="sell":
                    temp["sell"][elt['info']['future']] = elt['info']['size']
            return temp
        except Exception as e:
            write_logs(str(datetime.now()) + " ::: Error in balance position fetching: " + str(e))


    def get_symbol_position(self,symbol,position_side):
        try:
            write_logs(str(datetime.now()) + " ::: Getting symbol position for : " + symbol+" "+position_side)
            temp =  self.get_open_pos()
            if symbol in temp[position_side].keys():
                write_logs(str(datetime.now()) + " :::                  Position : " + temp[position_side][symbol])
                return float(temp[position_side][symbol])
            write_logs(str(datetime.now()) + " :::                  Position : O")
            return 0
        except Exception as e:
            write_logs(str(datetime.now()) + " ::: Error in balance position fetching for symbol: " + symbol+" "+str(e))


    def get_price(self,symbol):
        temp = self.ftx.fetch_ticker(symbol)
        prec = int(math.log10(1/float(temp['info']['sizeIncrement'])))
        last = float(temp['last'])
        return prec,last

    def post_open_pos(self,symbol,perc,side ='buy'):
        try:
            write_logs(str(datetime.now()) + " ::: Open order recieved for : " + symbol + " and side "+side )
            prec, last =  self.get_price(symbol)
            write_logs(str(datetime.now()) + " :::              Price for  : " + symbol + " is " + str(last))
            balance = self.get_balance()
            write_logs(str(datetime.now()) + " :::              balance is  : " + str(balance) +" and percentage is "+ str(perc) )
            amount = round(balance*perc/100/last,prec)
            write_logs(str(datetime.now()) + " :::              resulting amount is  : " + str(amount) )
            print(f'   Balance {balance} Last price {last} quantity {amount}')
            #side_ = "sell" if side == 'buy' else 'buy'
            temp1 = self.get_symbol_position(symbol,side)

            if temp1 and temp1 > 0:
                write_logs(str(datetime.now()) + " :::             Already in position : " + side)
            else:
                write_logs(str(datetime.now()) + " :::             Not in position, placing order  : " + side + " Amount is  : " + str(amount))
                res = self.ftx.create_market_order(symbol=symbol,side=side,amount=amount*leverage)
                write_logs(
                    str(datetime.now()) + " :::             Placing stop loss  : " + side + " Amount is  : " + str(
                        amount))
                sl = last*(1-stop_loss/100) if side =='buy' else last*(1+stop_loss/100)
                side_sl = 'sell' if side =='buy' else 'buy'
                self.ftx.create_order(symbol,'stop',side_sl,amount*leverage,params={'triggerPrice':sl,'reduceOnly': True})

                print( '   Order result = ',res)
            return amount
        except Exception as e:
            print("Erorr in placing long: "+str(e))
            write_logs(  str(datetime.now()) + " :::             Error  : " + str(e))

    def post_open_pos_qty(self,symbol,amount,side ='buy'):
        try:
            res = self.ftx.create_market_order(symbol=symbol,side=side,amount=amount)
            print( '   Order result = ',res)
            return amount
        except Exception as e:
            print("Erorr in closing previous long: "+str(e))


    def close_position(self,symbol,side ='buy'):
        try:
            write_logs(str(datetime.now()) + " ::: Close order recieved for : " + symbol + " and side " + side)
            # side_ = "sell" if side == 'buy' else 'buy'
            temp1 = self.get_symbol_position(symbol, side)
            if temp1 and temp1 > 0:
                side_ = "sell" if side == 'buy' else 'buy'
                write_logs(str(datetime.now()) + " :::             Already in position : " + side)
                res = self.post_open_pos_qty(symbol=symbol, side=side_, amount=temp1)
            else:
                write_logs(
                    str(datetime.now()) + " :::             Not in position")

        except Exception as e:
            print("Erorr in placing long: " + str(e))
            write_logs(str(datetime.now()) + " :::             Error  in closing : " + str(e))


