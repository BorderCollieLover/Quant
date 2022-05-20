# -*- coding: utf-8 -*-
"""
Created on Tue May 17 13:37:30 2022

@author: mtang
"""

import json
import datetime
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm


import quantlib.data_utils as data_utils
import quantlib.general_utils as general_utils

class ResidualMomemtum():
    
    #tickers = []
    #betas = []
    #returns = []
    #var_n = []
    cross_section_data = pd.DataFrame()
    
    def __init__(self,  market, index, var_len, stockdata_file, return_path, momentum_path):
        #self.update_name = update_name
        self.market = market
        self.var_len = var_len
        self.stockdata_file = stockdata_file # use stock info data from YFinance, which contains tickers and beta
        self.return_path = return_path
        self.momentum_path = momentum_path
        #self.momentum_ranking_path = momentum_ranking_path
        self.tickers =[]
        self.betas = []
        self.index = index # not necessary if using cross-sectional regression using beta

    #use stock info data from YFinance, select tickers and beta columns 
    #keep only tickers with beta
    def update_tickers(self):
        data = pd.read_csv(self.stockdata_file, index_col=0)
        data = data[['marketCap', 'averageVolume', 'fiftyDayAverage', 'beta']]
        data['hasna'] = [ np.isnan(data.loc[ticker,'beta']) for ticker in data.index]
        data= data[data['hasna'] == False]
        self.cross_section_data = pd.DataFrame(data=None, index=data.index, columns = ['Date', 'Beta', 'Ret', 'Var', 'Momentum', 'Ranking'])
        #self.tickers = data.index
        self.cross_section_data['Beta'] = data['beta']
                
        return
    
    def update_returns(self):
        #if (len(self.tickers)<=0):
        #    self.update_tickers()
        if self.cross_section_data.empty:
            self.update_tickers()
        #momentum_data = pd.DataFrame(data=None, index=self.tickers, columns = ['Date', 'Beta', 'Ret', 'Var'])
        for ticker in self.cross_section_data.index:
            return_file = self.return_path + "\\" + ticker + ".csv"
            try:
                return_data = pd.read_csv(return_file, index_col=0, parse_dates=[0])
            except Exception as e:
                #return_data = None
                print(e)
                continue
                
            #if (return_data == None):
            #    continue
            
            self.cross_section_data.at[ticker, 'Date']= return_data.index[-1]
            self.cross_section_data.at[ticker, 'Ret']= return_data['SimpleRet'][-1]
            self.cross_section_data.at[ticker, 'Var']= np.sqrt(np.average(return_data['Var1'][-self.var_len:]))
            #self.cross_section_data.at[ticker, 'Var']= self.betas[ticker]
         
        latest_dt = max(self.cross_section_data['Date'])
        self.cross_section_data['Ret'].mask(self.cross_section_data['Date']!=latest_dt, np.nan, inplace=True)
        self.cross_section_data['Ret']= pd.to_numeric(self.cross_section_data['Ret'])
        
        return(self.cross_section_data)
    
    def residual_momentum():
        
        return
        
            
hk_residualmomentum = ResidualMomemtum("HK", "HSI", 20, "V:\\HKExFilings\\StockInfo\\HKSecuritiesData.csv", "V:\\Daily\\Return", "V:\\Daily\\Momentum")
#hk_residualmomentum.update_returns
tmp = hk_residualmomentum.update_returns()
            
        
            
            
            
            
    
        
