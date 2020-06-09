# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 15:47:59 2020

@author: ARPIT
"""
#Manually created modules
import c_and_r            #reporting mechanism and data quality calculation
import newformat          #resample format
import KEY_BINANCE        #we have stored API keys here
import GetSym             #helper module

import os
import pymongo            
import time 
# import dns
from datetime import datetime
from pymongo import MongoClient
from binance.client import Client 
from binance.websockets import BinanceSocketManager
 
#for .env file where we store imp info and set variables
from dotenv import load_dotenv
load_dotenv()


#Retrieving the Keys
PUBLIC = KEY_BINANCE.Binance_API_Key
SECRET = KEY_BINANCE.Binance_Secret_Key

#Instantiating a Client 
client = Client(api_key=PUBLIC, api_secret=SECRET)

# current date and time
now = datetime.now() 

#to obtain just the minute part of time
st_min = (int)(now.strftime("%M"))
st_h = (int)(now.strftime("%H")) 

global x
x=1

# running dictionaries for storing recent data for resampling
symdic5 = GetSym.get_symbol_dict()
symdic15 = GetSym.get_symbol_dict()
symdic30 =  GetSym.get_symbol_dict()
symdic60 = GetSym.get_symbol_dict()

# getting current timestamp
sym = GetSym.get_sym_time(st_min)

# will hold per-symbol datapoint report
report={}

#Instantiating a BinanceSocketManager, passing in the client
bm = BinanceSocketManager(client)

URL2 = os.getenv("MONGO_DB_URL")
# URL1  = "mongodb://localhost:27017/"

# we create our MongoDB database here
try: 
    conne = MongoClient(URL2) 
    print("Connected successfully!!!") 
except pymongo.errors.ConnectionFailure as err:
    print(err)

# conne.server_info()
db = conne.database 
    
#the callback_function   
def process_message(msg):
    
    if msg['data']['e'] == 'error':    
        print(msg['data']['m'])
    
    else:
        
        #to convert date_time to readable format
        timestamp = msg['data']['k']['t']/1000
        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        #chk variable is used for regulating per minute data flow
        chk = (int)(timestamp[14]+timestamp[15])
        
        #getting the data in the format required
        dataframe={}
        dataframe['Time'] = timestamp; 
        dataframe['Symbol'] = msg['data']['k']['s']
        aux = dataframe['Symbol']  #for further use
        # print(aux)
        dataframe['Open'] = (float)(msg['data']['k']['o'])
        dataframe['High'] = (float)(msg['data']['k']['h'])
        dataframe['Low'] = (float)(msg['data']['k']['l'])
        dataframe['Close'] = (float)(msg['data']['k']['c'])
        dataframe['Volume'] = (float)(msg['data']['k']['v'])
        # print(dataframe)
        
        #condition so that data is entered per minute only
        if(chk>sym[aux] or (chk==0 and sym[aux]==59)):
            if(chk==0 and sym[aux]==59):
                sym[aux]=-1
            sym[aux] = (sym[aux]+1)
            db.stock1.insert_one(dataframe)
            print("Doc inserted in stock1")
            
            #to keep count of entries per symbol
            if(aux in report):
                report[aux] += 1
            else:
                report[aux] = 1
                
            symdic5[aux].append(dataframe)
            
            #to resample for 5 min interval using 1 min entries
            if(len(symdic5[aux])==5):
                new5=newformat.new_entry(symdic5[aux])
                db.stock5.insert_one(new5)
                print("Doc inserted in stock5")
                symdic15[aux].append(new5)
                symdic5[aux].clear()
            
            #to resample for 15 min interval using 5 min entries
            if(len(symdic15[aux])==3):
                new15=newformat.new_entry(symdic15[aux])
                db.stock15.insert_one(new15)
                print("Doc inserted in stock15")
                symdic30[aux].append(new15)
                symdic15[aux].clear()
                
            #to calculate for 30 min interval using 15 min entries
            if(len(symdic30[aux])==2):
                new30=newformat.new_entry(symdic30[aux])
                db.stock30.insert_one(new30)
                print("Doc inserted in stock30")
                symdic60[aux].append(new30)
                symdic30[aux].clear()
             
            #to calculate for 1 hour interval using 30 min entries
            if(len(symdic60[aux])==2):
                new60=newformat.new_entry(symdic60[aux])
                db.stock60.insert_one(new60)
                print("Doc inserted in stock60")
                symdic60[aux].clear()
            
            #process to calculate time to send report mail
            global x
            en_h = (int)(datetime.now().strftime("%H"))
            en_m = (int)(datetime.now().strftime("%M"))
            tot_time = (en_h - st_h)*60 + (en_m - st_min)
            # (int)(os.getenv("TIME_TO_SEND_MAIL"))
            mailtime = (int)(os.getenv("TIME_TO_SEND_MAIL"))
            if(tot_time == x*(mailtime)):
                x+=1
                print("{} minutes over. Check mail!!".format(mailtime))
                c_and_r.calculate_and_report(tot_time, report)
                
                
#establishing multiplex soxket connection for parallel run of multiple streams
connection_key = bm.start_multiplex_socket(GetSym.get_symbol_streams(), process_message)

#starting the socket manager 
bm.start()
print("data flowing in...")
#added to let some data flow, else periodically run the whole program
time.sleep((int)(os.getenv("TIME_TO_RUN")))


#stop the socket manager
bm.stop_socket(connection_key)

print("Data Run Complete")
#some data might come even after this because the process is asynchronous in nature


