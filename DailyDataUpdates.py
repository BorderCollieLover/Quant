# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 13:46:22 2022

@author: mtang
"""

import json
import datetime
import pandas as pd
import numpy as np


import quantlib.data_utils as data_utils
import quantlib.general_utils as general_utils


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
            
            df_sp500.to_excel(self.ticker_file_path+"\\Archive\\SP500 "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            df_sp500_chg.to_excel(self.ticker_file_path+"\\Archive\\SP500 Change "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            df_ndq.to_excel(self.ticker_file_path+"\\Archive\\NDQ "+datetime.datetime.today().strftime("%Y%m%d")+".xlsx",engine="openpyxl", index=False)
            
            sp500_tickers = list(df_sp500['Symbol'])
            sp500_chg_tickers = list(df_sp500_chg['Added Ticker'])
            ndq_tickers = list(df_ndq['Ticker'] )
            
            sp500_tickers = [x for x in sp500_tickers if pd.isnull(x) == False]
            sp500_chg_tickers = [x for x in sp500_chg_tickers if pd.isnull(x) == False]
            ndq_tickers = [x for x in ndq_tickers if pd.isnull(x) == False]
            
            all_tickers = list(set(sp500_tickers+sp500_chg_tickers +ndq_tickers ))
            all_tickers = sorted(list(map(lambda x: str.replace(x, ".", "-"), all_tickers)))
            
            us_ticker_file = self.ticker_file_path + "\\USTickers.csv"
            us_ticker_archive = self.ticker_file_path + "\\Archive\\USTickers " + datetime.datetime.today().strftime("%Y%m%d")+".csv"
            
            with open(us_ticker_file, "w") as outfile:
                outfile.write("\n".join(all_tickers))
                
            with open(us_ticker_archive, "w") as outfile:
                outfile.write("\n".join(all_tickers))
            
            self.tickers = all_tickers
        else:
            if (self.market == "HK"):
                hk_equities_datafile = self.ticker_file_path + "\\HKSecuritiesData.xlsx"
                df = pd.read_excel(hk_equities_datafile, header=0, index_col=0,  engine="openpyxl")
                hk_etf_datafile = self.ticker_file_path + "\\HKETFData.xlsx"
                df1 = pd.read_excel(hk_etf_datafile, header=0, index_col=0,  engine="openpyxl")
                
                self.tickers = sorted(list(df.index)+list(df1.index))
            else:
                if (self.market == "CN"):
                    sz_equities_datafile = self.ticker_file_path + "\\SZSecuritiesData.xlsx"
                    df = pd.read_excel(sz_equities_datafile, header=0, index_col=0,  engine="openpyxl")
                    sh_equities_datafile = self.ticker_file_path + "\\SHSecuritiesData.xlsx"
                    df1 = pd.read_excel(sh_equities_datafile, header=0, index_col=0,  engine="openpyxl")
                
                    self.tickers = sorted(list(df.index)+list(df1.index))
                else:
                    if (self.market =="Indices") : 
                        index_file = self.ticker_file_path + "\\GlobalIndices.csv"
                        df1 = pd.read_csv(index_file, header=None)
                        self.tickers = sorted(list(df1[0]))
                
                
        return
    
        
    def update_ohlc(self):
        #update the ohlc files for tickers
        if (len(self.tickers) <=0):
            self.update_tickers()

        for ticker in list(self.tickers):
            #print(ticker)
            output_file = self.raw_data_path + "\\" + ticker + ".csv"
            if general_utils.check_file_exists(output_file):
                try:
                    df1 = pd.read_csv(output_file, header=0, index_col=0, parse_dates=[0])                
                    last_dt = df1.index[-1]
                    ndays_to_retrieve = (datetime.datetime.now() - last_dt).days + 10      
                    df = data_utils.get_yf_daily_ohlcv(ticker, str(ndays_to_retrieve)+"d")
                    if not df.empty:
                        #check if there are dividend/split events in retrieved data
                        #yfinance returns dividend/split adjusted data by default 
                        #hence in case of corp action, the entire history needs to be re-download
                        corp_action = sum(df['dividends']) + sum(df['stocksplits'])
                        if (corp_action >0):
                            df = data_utils.get_yf_daily_ohlcv(ticker)
                        else:
                            df = df.combine_first(df1)
                        df.to_csv(output_file)
                except Exception as e: 
                    print(e)
                    df = data_utils.get_yf_daily_ohlcv(ticker)
                    if not df.empty:
                        df.to_csv(output_file)
            else:
                df = data_utils.get_yf_daily_ohlcv(ticker)
                if not df.empty:
                    df.to_csv(output_file)
                
        return
    
    def update_adjusted(self):
        #update adjusted ohlc files, adjusting for dividend and splits
        #pass for now -- yfinance downloads dividend/split adjusted OHLCV by default 
        return
        
        

hk_yf_update = YF_OHLC_Update("HK Update", "HK", "V:\\HKExFilings\\StockInfo", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")
hk_yf_update.update_ohlc()

us_yf_update = YF_OHLC_Update("US Update", "US", "V:\\Daily\\USTickers", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")
us_yf_update.update_ohlc()

cn_yf_update = YF_OHLC_Update("CN Update", "CN", "V:\\HKExFilings\\StockInfo", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")
cn_yf_update.update_ohlc()

index_yf_update = YF_OHLC_Update("Index Update", "Indices", "V:\\Daily", "V:\\Daily\\OHLC", "V:\\Daily\\Adjusted")
index_yf_update.update_ohlc()
    
           
        
