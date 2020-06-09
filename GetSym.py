# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 23:26:52 2020

@author: ARPIT
"""

import requests
import json

BASE_URL = 'https://api.binance.com'
resp = requests.get(BASE_URL + '/api/v1/ticker/allBookTickers')
tickers_list = json.loads(resp.content)

def get_symbol_dict():
    
    symbols = []
    for ticker in tickers_list:
        symbols.append((ticker['symbol']))
    
    symdic={}
    for sy in symbols:
        symdic.update({sy : []})
    
    return symdic

def get_symbol_streams():
    
    symbols = []
    for ticker in tickers_list:
        symbols.append((ticker['symbol']).lower()+'@kline_1m')
        
    return symbols

def get_sym_time(tm):
        
    symbols = []
    for ticker in tickers_list:
        symbols.append((ticker['symbol']))
    
    symdic={}
    for sy in symbols:
        symdic.update({sy : tm})
    
    return symdic
