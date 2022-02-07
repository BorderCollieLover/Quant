# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 13:46:22 2022

@author: mtang
"""

import json
import quantlib.data_utils as data_utils


class YF_OHLC_Update():
    def __init__(self, update_name, market, ticker_file_path, raw_data_path, adjusted_data_path):
        self.update_name = update_name
        self.market = market
        self.ticker_file_path = ticker_file_path
        self.raw_data_path = raw_data_path
        self.adjusted_data_path = adjusted_data_path
        self.tickers =[]

    def update_tickers(self):
        #For US stocks: get sp500 tickers and sp500 changes and save the table to ticker directory
        #For HK stocks: examine the YF
        #update the self.tickers list
        if (self.market =="US") : 
            df_sp500 = data_utils.get_sp500_instruments()
            df_sp500_chg = data_utils.get_sp500_changes()
            df_ndq = data_utils.get_ndq_instruments()
            
            
        return
    
        
    def update_ohlc(self):
        #update the ohlc files for tickers 
        return
    
    def update_adjusted(self):
        #update adjusted ohlc files, adjusting for dividend and splits
        return
        
        
        
us_yf_update = YF_OHLC_Update("US Update", "US", "V:\\Daily\\USTickers", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")

        
        
