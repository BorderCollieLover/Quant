# -*- coding: utf-8 -*-
"""
Created on Wed May 11 13:48:38 2022

@author: mtang
"""

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


class PCY():
    
    def __init__(self, ticker, alpha, ma_short, ma_long, ohlc_file_path, output_file_path):
        self.ohlc_file_path = ohlc_file_path
        self.output_file_path = output_file_path
        self.ticker = ticker
        self.alpha = alpha
        self.data = pd.DataFrame()
        self.ma_short = ma_short # small moving average 
        self.ma_long = ma_long # large moving average
        
        

    
    def pcy(self):
        #1. read the ohlc data
        self.ohlc = pd.read_csv(self.ohlc_file_path +"\\"+ self.ticker + ".csv", index_col=0, header=0,parse_dates=[0])
        
        self.ohlc['MAK'] 
        return
    

    
