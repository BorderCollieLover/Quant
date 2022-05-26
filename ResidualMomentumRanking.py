# -*- coding: utf-8 -*-
"""
Created on Tue May 17 13:37:30 2022

@author: mtang
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
import os



class ResidualMomemtum():
    
    #tickers = []
    #betas = []
    #returns = []
    #var_n = []
    cross_section_data = pd.DataFrame()
    
    def __init__(self,  market, index, var_len, stockdata_file, return_path, momentum_path):
        self.market = market
        self.var_len = var_len
        self.stockdata_file = stockdata_file # use stock info data from YFinance, which contains tickers and beta
        self.return_path = return_path
        self.momentum_path = momentum_path
        self.tickers =[]
        self.betas = []
        self.index = index # not necessary if using cross-sectional regression using beta
        self.momentum_file = self.momentum_path + "\\" + self.market + " Momentum.csv"
        self.momentumrank_file = self.momentum_path + "\\" + self.market + " Momentum Rank.csv"


    #use stock info data from YFinance, select tickers and beta columns 
    #keep only tickers with beta
    def update_tickers(self):
        data = pd.read_csv(self.stockdata_file, index_col=0)
        data = data[['marketCap', 'averageVolume', 'fiftyDayAverage', 'beta']]
        data['hasna'] = [ np.isnan(data.loc[ticker,'beta']) for ticker in data.index]
        data= data[data['hasna'] == False]
        self.cross_section_data = pd.DataFrame(data=None, index=data.index, columns = ['Date', 'Beta', 'Ret', 'Var', 'Momentum', 'Ranking'])
        self.cross_section_data['Beta'] = data['beta']
                
        return
    
    def update_returns(self, date_offset=0):
        if self.cross_section_data.empty:
            self.update_tickers()
        
        for ticker in self.cross_section_data.index:
            return_file = self.return_path + "\\" + ticker + ".csv"
            try:
                return_data = pd.read_csv(return_file, index_col=0, parse_dates=[0])
            except Exception as e:
                print(e)
                continue
            
            self.cross_section_data.at[ticker, 'Date']= return_data.index[(-1-date_offset)]
            self.cross_section_data.at[ticker, 'Ret']= return_data['SimpleRet'][(-1-date_offset)]
            self.cross_section_data.at[ticker, 'Var']= np.sqrt(np.average((return_data['Var1'][(-self.var_len-date_offset):])[:self.var_len]))
            #if np.isnan(self.cross_section_data.at[ticker, 'Var']):
            #    self.cross_section_data.at[ticker, 'Var'] = np.inf
            #np.sqrt(np.average(return_data['Var1'][(-var_len-date_offset):(-date_offset)]))
        
        latest_dt = max(set(list(self.cross_section_data['Date'])), key=list(self.cross_section_data['Date']).count)
        self.cross_section_data['Ret'].mask(self.cross_section_data['Date']!=latest_dt, np.nan, inplace=True)
        self.cross_section_data['Ret']= pd.to_numeric(self.cross_section_data['Ret'])
        
        return(self.cross_section_data)
   
    def residual_momentum(self):
        if self.cross_section_data.empty:
            self.update_returns()
            
        #cross section return regression versus beta
        #normalize residual by the variance of each underlying 
        try:
            regress_result = sm.ols(formula="Ret ~ Beta", data=self.cross_section_data,missing='drop').fit()
            regress_resid = regress_result.resid
            self.cross_section_data.loc[regress_resid.index, 'Momentum'] = regress_resid
            self.cross_section_data['Momentum'] = self.cross_section_data['Momentum']/self.cross_section_data['Var']
            self.cross_section_data.dropna(subset=['Momentum'], inplace=True)
            self.cross_section_data['Ranking'] = self.cross_section_data['Momentum'].rank( pct=True)
        except Exception as e: 
            print(e)
            
            
        latest_dt = max(set(list(self.cross_section_data['Date'])), key=list(self.cross_section_data['Date']).count)
        new_tickers = self.cross_section_data.index
        #update the momentum file and ranking file
        #
        if os.path.exists(self.momentum_file):
            momentum_data = pd.read_csv(self.momentum_file, header=0,index_col=0, parse_dates=[0])
            rank_data = pd.read_csv(self.momentumrank_file, header=0,index_col=0, parse_dates=[0])
            
            existing_tickers = list(momentum_data.columns)
            
            ticker_additions = list(set(new_tickers) - set(existing_tickers))
            if len(ticker_additions)>0:
                for ticker in ticker_additions: 
                    momentum_data[ticker]=np.nan
                    rank_data[ticker]=np.nan
            
            if latest_dt not in momentum_data.index:
                momentum_data.append(pd.Series(name=latest_dt))
                rank_data.append(pd.Series(name=latest_dt))
        else:
            dt_index = [latest_dt]
            momentum_data = pd.DataFrame(data=None, index=dt_index, columns = new_tickers)
            rank_data = pd.DataFrame(data=None, index=dt_index, columns = new_tickers)
            
        momentum_data.loc[latest_dt, new_tickers] = self.cross_section_data.loc[new_tickers, 'Momentum']
        rank_data.loc[latest_dt, new_tickers] = self.cross_section_data.loc[new_tickers, 'Ranking']
        
        momentum_data.sort_index(inplace=True)
        rank_data.sort_index(inplace=True)
        
        momentum_data.to_csv(self.momentum_file)
        rank_data.to_csv(self.momentumrank_file)
                         
        return(self.cross_section_data)
    
    def HistMomentum(self):
        self.update_tickers()
        
        for i in range(100):
            self.update_returns(date_offset=i)
            self.residual_momentum()
            
        return (self.cross_section_data)
        
            
hk_residualmomentum = ResidualMomemtum("HK", "HSI", 20, "V:\\HKExFilings\\StockInfo\\HKSecuritiesData.csv", "V:\\Daily\\Return", "V:\\Daily\\Momentum")
tmp = hk_residualmomentum.residual_momentum()
#tmp = hk_residualmomentum.HistMomentum()

            
        
            
            
            
            
    
        
