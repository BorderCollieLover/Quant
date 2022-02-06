import json
import numpy as np
import pandas as pd

#python3 -m pip install scipy
from scipy.stats import skew

import quantlib.general_utils as general_utils
import quantlib.indicators_cal as indicators_cal
import quantlib.backtest_utils as backtest_utils
import quantlib.diagnostics_utils as diagnostics_utils


"""
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3247865
"""

class Skprm():

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target, brokerage_used):
        self.pairs = [(23, 82), (44, 244), (124, 294), (37, 229), (70, 269), (158, 209), (81, 169), (184, 203), (23, 265), (244, 268), (105, 106), (193, 250), (127, 294), (217, 274), (45, 178), (103, 288), (204, 248), (142, 299), (71, 216), (129, 148), (149, 218)]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target
        self.brokerage_used = brokerage_used
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)
        self.sysname = "SKPRM"    

    def extend_historicals(self, instruments, historical_data):
        #get skew for each date
        for date in historical_data.index:
            for inst in instruments:
                #some lookback period to measure skew
                rolling_returns = historical_data.loc[:date].tail(60)["{} % ret".format(inst)]
                skewness = skew(rolling_returns)
                historical_data.loc[date, "{} skew".format(inst)] = skewness
        return historical_data
    
    def run_simulation(self, historical_data, debug=False, use_disk=False):
        """
        Init & Pre-processing
        """
        #lets try running the strategy for fx, commodities and metals
        instruments = self.instruments_config["commodities"] + self.instruments_config["metals"]
        historical_data = self.extend_historicals(instruments=instruments, historical_data=historical_data)
        portfolio_df = pd.DataFrame(index=historical_data[self.simulation_start:].index).reset_index()
        portfolio_df.loc[0, "capital"] = 10000
        is_halted = lambda inst, date: not np.isnan(historical_data.loc[date, "{} active".format(inst)]) and \
            (~historical_data[:date].tail(5)["{} active".format(inst)]).all() 
        
        """
        Position Sizing with 3 different techniques combined
        1. Strategy Level scalar for strategy level risk exposure
        2. Volatilty targeting scalar for different assets
        3. Voting system to account for degree of `momentum'
        """
        if use_disk:
            portfolio_df = general_utils.load_file(
                "./backtests/{}_{}.obj".format(self.brokerage_used, self.sysname)
            )
            return portfolio_df, instruments
            
        for i in portfolio_df.index:
            date = portfolio_df.loc[i, "date"]
            strat_scalar = 2 #default scaling up for strategy

            tradable = [inst for inst in instruments if not is_halted(inst, date)]
            non_tradable = [inst for inst in instruments if inst not in tradable]

            """
            Get PnL and Scalar for Portfolio
            """
            if i != 0:
                date_prev = portfolio_df.loc[i - 1, "date"]
                pnl = backtest_utils.get_backtest_day_stats(\
                    portfolio_df, instruments, date, date_prev, i, historical_data)
                strat_scalar = backtest_utils.get_strat_scaler(\
                    portfolio_df, 100, self.vol_target, i, strat_scalar)
            
            portfolio_df.loc[i, "strat scalar"] = strat_scalar

            """
            Get Positions for Traded Instruments, Assign 0 to Non-Traded
            """
            for inst in non_tradable:
                portfolio_df.loc[i, "{} units".format(inst)] = 0
                portfolio_df.loc[i, "{} w".format(inst)] = 0

            skews = {}
            for inst in tradable:
                skews[inst] = historical_data.loc[date, "{} skew".format(inst)]
            #sort the skew based on skewness in increasing order
            skews = {k:v for k,v in sorted(skews.items(), key=lambda pair:pair[1])}
            quantile_size = int(len(tradable) * 0.25)
            high_skewness = list(skews.keys())[-quantile_size:]
            low_skewness = list(skews.keys())[:quantile_size]

            nominal_total = 0
            for inst in tradable:
                #long bottom skew quantile, short top skew quantile
                forecast = 0
                forecast = 1 if inst in low_skewness else forecast
                forecast = -1 if inst in high_skewness else forecast

                #volatility targetting
                position_vol_target = (1 / len(tradable)) * portfolio_df.loc[i, "capital"] * self.vol_target / np.sqrt(253)
                inst_price = historical_data.loc[date, "{} close".format(inst)]
                percent_ret_vol = historical_data.loc[date, "{} % ret vol".format(inst)] \
                    if historical_data[:date].tail(25)["{} active".format(inst)].all() else 0.025
                dollar_volatility = backtest_utils.unit_val_change(inst, inst_price * percent_ret_vol , historical_data, date)
                position = strat_scalar * forecast * position_vol_target / dollar_volatility
                portfolio_df.loc[i, "{} units".format(inst)] = position
                nominal_total += abs(position * backtest_utils.unit_dollar_value(inst, historical_data, date))
                
            for inst in tradable:
                units = portfolio_df.loc[i, "{} units".format(inst)]
                nominal_inst = units * backtest_utils.unit_dollar_value(\
                    inst, historical_data, date)
                inst_w = nominal_inst / nominal_total
                portfolio_df.loc[i, "{} w".format(inst)] = inst_w
            
            """
            Perform Logging and Calculations
            """
            portfolio_df.loc[i, "nominal"] = nominal_total
            portfolio_df.loc[i, "leverage"] = portfolio_df.loc[i, "nominal"] / portfolio_df.loc[i, "capital"]
     
            if debug: print(portfolio_df.loc[i])
        
        portfolio_df.set_index("date", inplace=True)

        diagnostics_utils.save_backtests(
            portfolio_df=portfolio_df,
            instruments=instruments,
            brokerage_used=self.brokerage_used,
            sysname=self.sysname
        )
        diagnostics_utils.save_diagnostics(
            portfolio_df=portfolio_df,
            instruments=instruments,
            brokerage_used=self.brokerage_used,
            sysname=self.sysname
        )
        return portfolio_df, instruments

    def get_subsys_pos(self, debug=False, use_disk=False):
        portfolio_df, instruments = self.run_simulation(historical_data=self.historical_df, debug=debug, use_disk=use_disk)
        return portfolio_df, instruments

"""
Comment on Skewness Premiums
The strategy still yields positive return, but not by alot.
Actually, the strategy implementation documented in the paper 151 Strategies...
is a naive version. Commodity skew premia is well documented.

The skewness factor is usually composed of two different constituents, that is
the market skewness and the idiosynractic skewness.

Improved variants of the skewness premium harvesting focuses on the idiosyncratic
component. We do this by implementing a one-factor model or multi-factor model
with market indices, such as Goldman Sachs Commodity Index (GSCI) and performing
skewness computation on the residuals, as opposed to just returns.

This has (historically) proved better results. To do this, one can create their
own index, or in the extend_dataframe method, poll yahoo finance GSCI prices

Other information required can also similarly be obtained or added to the dataframe
or supplemented in the extend_dataframe method. for instance, if you have 
a neural model making price predictions, you can, load it inside there etc.

We will stick with the vanilla version for now, which according to our backtest
yields a Sharpe of 0.20. Note that low Sharpe strategies like this can stay
MANY years underwater.
"""