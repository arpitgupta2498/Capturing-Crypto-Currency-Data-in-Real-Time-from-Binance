# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 12:34:18 2020

@author: ARPIT
"""


# This module includes methods to resample the data entries into required intervals

def new_time(df):
     return df[0]['Time']

def new_symbol(df):
    return df[0]['Symbol']
    
def new_open(df):
    return df[0]['Open']

def new_high(df):
    maxx=-1
    for entry in df:
        maxx = max(maxx,entry['High'])
    return maxx

def new_low(df):
    minn=1000000000
    for entry in df:
        minn = min(minn, entry['Low'])
    return minn

def new_close(df):
    return df[len(df)-1]['Close']

def new_vol(df):
    summ = 0
    for entry in df:
        summ = summ + (entry['Volume'])
    return summ

#we return the resampled entry in the same format as required
def new_entry(df):
    return ({'Time': new_time(df), 'Symbol': new_symbol(df), 'Open': new_open(df),
            'High': new_high(df), 'Low': new_low(df), 'Close': new_close(df), 'Volume': new_vol(df)})
    