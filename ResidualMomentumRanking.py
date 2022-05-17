# -*- coding: utf-8 -*-
"""
Created on Tue May 17 13:37:30 2022

@author: mtang
"""

import json
import datetime
import pandas as pd
import numpy as np


import quantlib.data_utils as data_utils
import quantlib.general_utils as general_utils

class ResidualMomemtum():
    
    tickers = []
    betas = []
    
    def __init__(self, update_name, market, index, stockdata_file, ohlc_path, momentum_path, momentum_ranking_path):
        self.update_name = update_name
        self.market = market
        self.stockdata_file = stockdata_file # use stock info data from YFinance, which contains tickers and beta
        self.ohlc_path = ohlc_path
        self.momentum_path = momentum_path
        self.momentum_ranking_path = momentum_ranking_path
        self.tickers =[]
        self.betas = []
        self.index = index # not necessary if using cross-sectional regression using beta

    #use stock info data from YFinance, select tickers and beta columns 
    #keep only tickers with beta
    def update_tickers(self):
        if (self.market =="US") : 
            
            data = pd.read_excel(USStockInfoDir+ "USTickers.csv", header=None)
            ustickers = list(data[0])
            
            self.tickers = sorted(all_tickers)
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
    
        
