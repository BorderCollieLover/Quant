# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 13:46:22 2022

@author: mtang
"""

import json
import quantlib.data_utils as data_utils
import datetime
import pandas as pd
import numpy as np




class YF_OHLC_Update():
    
    tickers = []
    
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
            
            df_sp500.to_excel(self.ticker_file_path+"\\SP500 "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            df_sp500_chg.to_excel(self.ticker_file_path+"\\SP500 Change "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            df_ndq.to_excel(self.ticker_file_path+"\\NDQ "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            
            
            sp500_tickers = list(df_sp500['Symbol'])
            sp500_chg_tickers = list(df_sp500_chg['Added Ticker'])
            ndq_tickers = list(df_ndq['Ticker'] )
            
            sp500_tickers = [x for x in sp500_tickers if pd.isnull(x) == False]
            #print('here2')
            sp500_chg_tickers = [x for x in sp500_chg_tickers if pd.isnull(x) == False]
            ndq_tickers = [x for x in ndq_tickers if pd.isnull(x) == False]

            
            self.tickers = sorted(list(set(sp500_tickers+sp500_chg_tickers +ndq_tickers )))
            
            #print(self.tickers)
        else:
            pass
        return
    
        
    def update_ohlc(self):
        #update the ohlc files for tickers
        if (len(self.tickers) <=0):
            self.update_tickers()
        
        #print(self.tickers)
        #print(len(self.tickers))
        for ticker in list(self.tickers):
            df = data_utils.get_yf_daily_ohlcv(ticker)
            if not df.empty:
                df.to_csv(self.raw_data_path + "\\" + ticker + ".csv")
            
        return
    
    def update_adjusted(self):
        #update adjusted ohlc files, adjusting for dividend and splits
        return
        
        
        
us_yf_update = YF_OHLC_Update("US Update", "US", "V:\\Daily\\USTickers", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")
us_yf_update.update_ohlc()


        
        
