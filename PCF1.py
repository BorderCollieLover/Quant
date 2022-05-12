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


class PCY_Update():
    
    tickers = []
    
    def __init__(self, alpha, ohlc_file_path, output_file_path):
        self.ohlc_file_path = ohlc_file_path
        self.output_file_path = output_file_path
        self.tickers =[]
        self.alpha = alpha

    
    def pcy
    def update(self):
        #update the ohlc files for tickers
        if (len(self.tickers) <=0):
            self.update_tickers()
            
        

        for ticker in list(self.tickers):
            #1. check if OHLC file exists, if not skip -- need OHLC
            #2. check if PCF file exists, if not -- calculate from beginning 
            #3. if both file exists, check if the PCF file is older, if yes, skip 
            #4. if no, calculate the updated part of PCF
            #print(ticker)
            output_file = self.output_file_path + "\\" + ticker + ".csv"
            ohlc_file = self.ohlc_file_path + "\\" + ticker + ".csv"
            if general_utils.check_file_exists(ohlc_file):
                if general_utils.check_file_exists(output_file):
                    try:
                        ohlc_df = pd.read_csv(ohlc_file, header=0, index_col=0, parse_dates=[0])                
                        last_dt = ohlc_df.index[-1]
                    except Exception as e: 
                        print (e)
                else:
                    #caclulate 
                    
                    # find the last date of the PCF 
                    #
                
        return
    
