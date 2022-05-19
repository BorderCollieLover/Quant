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
    returns = []
    var_n = []
    
    def __init__(self, update_name, market, index, var_len, stockdata_file, return_path, momentum_path, momentum_ranking_path):
        self.update_name = update_name
        self.market = market
        self.var_len = var_len
        self.stockdata_file = stockdata_file # use stock info data from YFinance, which contains tickers and beta
        self.return_path = return_path
        self.momentum_path = momentum_path
        self.momentum_ranking_path = momentum_ranking_path
        self.tickers =[]
        self.betas = []
        self.index = index # not necessary if using cross-sectional regression using beta

    #use stock info data from YFinance, select tickers and beta columns 
    #keep only tickers with beta
    def update_tickers(self):
        data = pd.read_csv(self.stockdata_file, index_col=0)
        data = data[['marketCap', 'averageVolume', 'fiftyDayAverage', 'beta']]
        data['hasna'] = [ np.isnan(data.loc[ticker,'beta']) for ticker in data.index]
        data = data[data['hasna'] == False]
        self.tickers = data.index
        self.betas = data['beta']
                
        return
    
    def update_returns(self):
        _data = pd.DataFrame(data=None, index=self.tickers, columns = ['Date', 'Ret', 'Var'])
        for ticker in self.tickers:
            return_file = self.return_path + "\\" + ticker + ".csv"
            try:
                return_data = pd.read_csv(return_file, index_col=0, parse_dates=[0])
            except Exception as e:
                return_data = None
                print(e)
                
            if (return_data == None):
                continue
            
            return_data.at[ticker, 'Date']= 
            
            
            
    
        
