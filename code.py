import csv
import json
from datetime import datetime
import requests
import os
import pandas as pd
import time

from ftx_handler import ftx_handler,percentage_of_balance
from binance_handler import binance_handler

m =  binance_handler()
#print(m.get_open_pos())

def write_logs(sentence):
    with open("logs.txt",'a') as fl :
        fl.write(sentence+'\n')
def write_logs(sentence):
    with open("logs.txt",'a') as fl :
        fl.write(sentence+'\n')
def trade_the_message(symbol="",position_status="",position_side="",entry_price=""):
    write_logs(str(datetime.now())+" ::: New message recieved: "+symbol+"  "+position_side+"  "+position_status+"  "+entry_price)
    side = 'buy' if position_side =="long" else "sell"
    if len(symbol) <=9:
        symbol=symbol.replace('USDT','-PERP')
    print(position_status,position_side in ['open'],position_side in ['reduce', 'close'])
    if position_status in ['open']:
        m.post_open_pos(symbol,perc=percentage_of_balance,side=side)
    elif position_status in ['reduce', 'close']:
        m.get_and_close_open_position(ticker=symbol)
    print(symbol,position_side,position_status,entry_price)



def task(encryptedUid,user):
    data={"encryptedUid":encryptedUid,"tradeType":"PERPETUAL"}
    data = str(data)
    data_changed = []
    new_data = []
    prev_creators = None
    new_symbols=[]
    prev_symbols=[]
    prev_amount={}
    start_time=datetime.now()
    print("Start Time:"+str(start_time))
    resp = requests.post("https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition",
                         data=data,
                         headers={
                             "Accept": "*/*",
                             "Accept-Language": "en-US,en;q=0.5",
                             "Connection": "keep-alive",
                             "Origin": "https://www.binance.com",
                             "TE": "Trailers",
                             "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",
                             "clienttype": "web",
                             "content-type": "application/json",
                         }
                         )
    data=json.loads(resp.content.decode())
    is_data = data.get('data')
    is_data=is_data.get('otherPositionRetList')
    curr_count=len(is_data)
    print("Current Count: {0} ".format(curr_count))
    prev_data = read_prev_data()
    print("Previous Count: {0} ".format(len(prev_data)))
    try:
        prev_count=len(prev_data)
        clear_data()
    except:
        prev_count=0

    #if prev_count and curr_count > prev_count:
    if is_data:
        print('here')
        #he alert should include position status (open or close), entry price, time, position side (Long or short), amount (size of the position).
        for item in is_data:
            entry_price=item.get('entryPrice')
            update_time=item.get('updateTime')
            symbol=item.get('symbol')
            size=item.get('amount')
            if str(size).__contains__('-'):
                position_side='short'
            else:
                position_side='long'
            output_data=[symbol,'open',position_side,str(size),str(entry_price),str(update_time)]
            #new_data.append(output_data)
            new_symbols.append(symbol)
            #compare_data = [symbol]
            path = os.getcwd()
            with open(path + '/creators_data.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(output_data)

            f.close()
            if len(prev_data) >= 0:
                if output_data not in prev_data:
                    print(output_data)
                    print(prev_data)
                    data_changed.append(output_data)
                    #url="https://www.binance.com/en/futures-activity/leaderboard?type=myProfile&encryptedUid="+encryptedUid
                    # base_url2 = "https://api.telegram.org/bot2003301423:AAGkEViPY7PNhTZ-g1NYzBqR0Ny1B0r_fH4/sendMessage?chat_id=-1001637572020&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                    #     symbol, 'open',position_side,size,entry_price,update_time,user)
                    # print(base_url2.replace("'", ""))
                    # requests.get(base_url2.replace("'", ""))
                    # end_time = datetime.now() - start_time
                    # t=end_time.seconds
                    # base_url2 = 'https://api.telegram.org/bot2003301423:AAGkEViPY7PNhTZ-g1NYzBqR0Ny1B0r_fH4/sendMessage?chat_id=-1001637572020&text="Alert Detected and Generated within {0} seconds"'.format(str(t))
                    # requests.get(base_url2)
                    # print("Successfully send")
    if len(prev_data) >= 0:
        for item in prev_data:
            prev_symbols.append(item[0])
            if item[3]:
                prev_amount.update(
                    {item[0]:item[3]}
                    )


    if len(data_changed) > 0:
        for item in data_changed:
            if item[0] in prev_symbols:
                if item[2] == 'long':
                    amount=prev_amount.get(item[0])
                    if float(amount) < float(item[3]):
                        position_status = 'add'
                        amount_size = float(item[3])-float(amount)
                        amount_range = '({0}-{1})'.format(str(amount), str(item[3]))
                        val1 = float(amount)
                        val2 = float(item[3])
                        val3= val2-val1
                        per_diff = 100 * (val3 / val1)
                        per_diff = round(per_diff, 5)
                        per_diff = str(per_diff).replace('-', '')

                        base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \n% change: {7} \nAmount: {8} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                            item[0], position_status, item[2], amount_range, item[4], item[5], user, str(per_diff),str(amount_size))
                        print(base_url2.replace("'", ""))
                        #requests.get(base_url2.replace("'", ""))
                        trade_the_message(symbol=item[0], position_status=position_status, position_side=item[2],entry_price=item[4])

                    if float(amount) > float(item[3]):
                        position_status = 'reduce'
                        amount_size = float(item[3])-float(amount)
                        amount_range = '({0}-{1})'.format(str(amount), str(item[3]))
                        val1 = float(amount)
                        val2 = float(item[3])
                        val3= val2-val1
                        per_diff = 100 * (val3 / val1)
                        per_diff = round(per_diff, 5)
                        if not str(per_diff).__contains__('-'):
                            per_diff = '-' + str(per_diff)
                        base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \n% change: {7} \nAmount: {8} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                            item[0], position_status, item[2], amount_range, item[4], item[5], user, str(per_diff),str(amount_size))
                        print(base_url2.replace("'", ""))
                        #requests.get(base_url2.replace("'", ""))
                        trade_the_message(symbol=item[0], position_status=position_status, position_side=item[2],entry_price=item[4])

                if item[2] == 'short':
                    amount = prev_amount.get(item[0])
                    p_amount=str(amount).replace('-','')
                    new_amount=str(item[3]).replace('-','')
                    if float(p_amount) < float(new_amount):
                        position_status = 'add'
                        amount_size = float(p_amount)-float(new_amount)
                        amount_range = '({0}-{1})'.format(str(amount), str(item[3]))
                        val1 = float(p_amount)
                        val2 = float(new_amount)
                        val3= val2-val1
                        per_diff = 100 * (val3 / val1)
                        per_diff = round(per_diff, 5)
                        if not str(per_diff).__contains__('-'):
                            per_diff = '-' + str(per_diff)
                        base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \n% change: {7} \nAmount: {8} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                            item[0], position_status, item[2], amount_range, item[4], item[5], user, str(per_diff),
                            str(amount_size))
                        print(base_url2.replace("'", ""))
                        #requests.get(base_url2.replace("'", ""))
                        trade_the_message(symbol=item[0], position_status=position_status, position_side=item[2], entry_price=item[4])

                    if float(p_amount) > float(new_amount):
                        position_status = 'reduce'
                        amount_size = float(p_amount)-float(new_amount)
                        amount_range = '({0}-{1})'.format(str(amount), str(item[3]))
                        val1 = float(p_amount)
                        val2 = float(new_amount)
                        val3= val2-val1
                        per_diff = 100 * (val3 / val1)
                        per_diff = round(per_diff, 5)
                        per_diff = str(per_diff).replace('-', '')

                        base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \n% change: {7} \nAmount: {8} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                            item[0], position_status, item[2], amount_range, item[4], item[5], user, str(per_diff),
                            str(amount_size))
                        print(base_url2.replace("'", ""))
                        #requests.get(base_url2.replace("'", ""))
                        trade_the_message(symbol=item[0], position_status=position_status, position_side=item[2],entry_price=item[4])
                # if str(amount) == str(item[3]):
                #     print("No Data Changed")
                    # base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                    #     item[0], 'open', item[2], item[3], item[4], item[5], user)
                    # print(base_url2.replace("'", ""))
                    # requests.get(base_url2.replace("'", ""))
                # else:
                #     amount_range = '({0}-{1})'.format(str(amount), str(item[3]))
                #     try:
                #         perc_close = float(amount)-float(item[3])
                #         perc_close = round(perc_close,2)
                #     except Exception as ex:
                #         print(ex)
                #         perc_close = ''
                #     print("Data Changed")
                #     base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \n% Close: {7} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                #         item[0], 'close', item[2], amount_range, item[4], item[5], user, str(perc_close))
                #     print(base_url2.replace("'", ""))
                #     requests.get(base_url2.replace("'", ""))

            else:
                print("Data Changed")
                base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                    item[0], 'open', item[2], item[3], item[4], item[5], user)
                print(base_url2.replace("'", ""))
                #requests.get(base_url2.replace("'", ""))
                trade_the_message(symbol=item[0], position_status='open', position_side=item[2],entry_price=item[4])

        # try:
        #     alert_msg = ["BINANCE ALERT DATA: {0}".format(data_changed)]
        #     base_url2 = "https://api.telegram.org/bot2003301423:AAGkEViPY7PNhTZ-g1NYzBqR0Ny1B0r_fH4/sendMessage?chat_id=-1001637572020&text='Symbol: {0} \nPosition Status: {1} \nPosition Side: {2} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
        #         currency, value, volume, market_time, diluted_market, market_cap)
        #     print(base_url2.replace("'", ""))
        #     requests.get(base_url2.replace("'", ""))
        #     print("Successfully send")
        #     #send_alert(alert_msg)
        # except Exception as ex:
        #     print(ex)
        #     pass
    else:
        print("No Data Changed")

    if len(prev_data) > 0:
        for item in prev_data:
            if item[0] not in new_symbols:
                base_url2 = "https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text='User: {6} \nSymbol: {0} \nPosition Status: {1} \nPosition Side: {2} \nAmount(Size): {3} \nEntry Price: {4} \nTime: {5} '".format(
                    item[0], 'closed', item[2], item[3], item[4], item[5], user)
                print(base_url2.replace("'", ""))
                #requests.get(base_url2.replace("'", ""))
                trade_the_message(symbol=item[0], position_status='close', position_side=item[2], entry_price=item[5])


    print("End Time" + str(datetime.now()))


def read_data(file_name):
    all_data = []
    if os.path.exists(file_name):
        data = pd.read_csv(file_name)
        creators = data.total_creators.tolist()
        if len(creators) > 0:
            return creators[0]
    else:
        path = os.getcwd()
        with open(path + '/creators_data.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(
                ["symbol","status","position_side","size","entry_price","update_time"])
        f.close()
    return all_data


def read_prev_data():
    data=[]
    try:
        path = os.getcwd()
        with open(path + '/creators_data.csv', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
            data = data[1:]
        f.close()
        data = [item for item in data if len(item)>0]
    except:
        pass
    return data


def clear_data():
    path = os.getcwd()
    try:
        with open(path + '/creators_data.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow()
        f.close()
    except:
        pass
    try:
        with open(path + '/creators_data.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(
                ["symbol","status","position_side","size","entry_price","update_time"])
        f.close()
    except:
        pass

def send_alert(alerts):
    for i in alerts:
        print(i)
        # base_url = 'https://api.telegram.org/bot2071740128:AAGMBV18aEOXRbGwlH5EKhgIwGnr21xQh50/sendMessage?chat_id=-1001750678072&text="{}"'.format(i)
        # requests.get(base_url)
        base_url2 = 'https://api.telegram.org/bot5066231999:AAEfOWw4UK0LgbV09OS68ZBed5flgK2M1Ww/sendMessage?chat_id=-1001792442944&text="{}"'.format(
            i)
        requests.get(base_url2)

if __name__ == '__main__':
    path=os.getcwd()
    file_name=path+'/input_url.txt'
    data=open(file_name,'r').read()
    data_split=data.split('#')
    user=data_split[1]
    encryptedUid = data_split[0].split('encryptedUid=')[1]
    while True:
        try:
            task(encryptedUid,user)
            time.sleep(1)
        except Exception as ex:
            print(ex)
            pass
