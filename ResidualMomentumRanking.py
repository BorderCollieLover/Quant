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
        data = pd.read_csv(self.stockdata_file, index_col=0)
        data = data[['marketCap', 'averageVolume', 'fiftyDayAverage', 'beta']]
        
        
                
                
        return
    
        
