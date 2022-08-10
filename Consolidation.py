# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 11:47:54 2022

@author: mtang
"""


import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
import os



class Consolidation():
    
    #tickers = []
    #betas = []
    #returns = []
    #var_n = []
   
    
    def __init__(self,  ticker, win_len, ohlc_file, return_file):
        self.win_len = win_len
        self.ohlc_file = ohlc_file # use stock info data from YFinance, which contains tickers and beta
        self.return_file = return_file
        self.ticker = ticker
        try:
            self.ohlc = pd.read_csv(self.ohlc_file, index_col=0)
        except Exception as e:
            print(e)
            self.ohlc = pd.DataFrame()
            
        try:
            self.ret = pd.read_csv(self.return_file, index_col=0)
        except Exception as e:
            print(e)
            self.ret = pd.DataFrame()
        
    def TestConsolidation(self, threshold, use_close=True, use_atr=True):
        #if use_close = False, consider the difference between highest high and lowest low of the look-back period
        #if use_close = True, consider the difference between highest close and the lowest close of the lookback period
        #if use_atr = False, consider the ratio of high over low and compare it to the theshold 
        #if use_atr = True, consider the difference between high and low, and compare it to threshold*atr
        
        if self.ohlc.empty:
            print("No OHLC data.")
            return
        
        if use_atr:
            if self.ret.emtpy:
                print("No ATR data.")
                return
            
        if use_close:
            self.high = max(self.ohlc[:-self.winlen, 'close'])
            self.low = min(self.ohlc[:-self.winlen, 'close'])
        else:
            self.high = max(self.ohlc[:-self.winlen, 'high'])
            self.low = min(self.ohlc[:-self.winlen, 'low'])
            
            
        
        return
    
    def HistoricalConsolidationValue(self, use_close=True, use_atr=True):
        return
        
        
    
   
