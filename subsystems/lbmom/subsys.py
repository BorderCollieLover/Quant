import json
import numpy as np
import pandas as pd

import quantlib.general_utils as general_utils
import quantlib.indicators_cal as indicators_cal
import quantlib.backtest_utils as backtest_utils
import quantlib.diagnostics_utils as diagnostics_utils

"""
https://hangukquant.substack.com/p/volatility-targeting-the-asset-level
https://hangukquant.substack.com/p/volatility-targeting-the-strategy
"""

class Lbmom():

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target, brokerage_used):
        self.pairs = [(23, 82), (44, 244), (124, 294), (37, 229), (70, 269), (158, 209), (81, 169), (184, 203), (23, 265), (244, 268), (105, 106), (193, 250), (127, 294), (217, 274), (45, 178), (103, 288), (204, 248), (142, 299), (71, 216), (129, 148), (149, 218)]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target #for more information on volatility targetting, refer to my post linked
        self.brokerage_used = brokerage_used
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)
        self.sysname = "LBMOM"    

    def extend_historicals(self, instruments, historical_data):
        for inst in instruments:
            historical_data["{} adx".format(inst)] = indicators_cal.adx_series(
                high=historical_data[inst + " high"], 
                low=historical_data[inst + " low"], 
                close=historical_data[inst + " close"],
                n = 14
            )
            for pair in self.pairs:
                historical_data["{} ema{}".format(inst, str(pair))] = indicators_cal.ema_series(
                    series = historical_data[inst + " close"],
                    n = pair[0]
                ) - indicators_cal.ema_series(
                    series = historical_data[inst + " close"],
                    n = pair[1]
                ) 
        return historical_data    
    
    def run_simulation(self, historical_data, debug=False, use_disk=False):
        """
        Init & Pre-processing
        """
        instruments = self.instruments_config["equities"] + self.instruments_config["indices"] + self.instruments_config["bonds"]
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

            nominal_total = 0
            for inst in tradable:
                #lets make this abit clear
                votes = np.sum([1 for pair in self.pairs if historical_data.loc[date, "{} ema{}".format(inst, str(pair))] > 0])
                forecast = votes / len(self.pairs) #1 is all `trending`. 0 is none `trending`
                #check if regime is trending else cast 0 vote for all. if adx < 25, consider as `not trending`
                forecast = 0 if historical_data.loc[date, "{} adx".format(inst)] < 25 else forecast 

                #volatility targetting
                position_vol_target = (1 / len(tradable)) * portfolio_df.loc[i, "capital"] * self.vol_target / np.sqrt(253)
                inst_price = historical_data.loc[date, "{} close".format(inst)]
                percent_ret_vol = historical_data.loc[date, "{} % ret vol".format(inst)] \
                    if historical_data[:date].tail(25)["{} active".format(inst)].all() else 0.025
                dollar_volatility = backtest_utils.unit_val_change(inst, inst_price * percent_ret_vol , historical_data, date)
                position = strat_scalar * forecast * position_vol_target / dollar_volatility
                portfolio_df.loc[i, "{} units".format(inst)] = position
                nominal_total += abs(position * backtest_utils.unit_dollar_value(\
                    inst, historical_data, date))
                
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


#now we want to run the simulation.
#we are also adopting a risk management technique at the asset and strategy level called
#vol targeting, where we lever our capital in order to achieve a certain `target` annualized
#voltility, and the relative allocations are inversely proportional to the volatility of the
#asset/

#the reasoning is simple: assume volatility is a proxy for risk, we want to assign a similar
#amount of `risk` to each position. We do not want any particular position to have outsized
#impacts on the overall portfolio, hence the term volatility targetting.

"""
percent_ret_vol = historical_data.loc[date, "{} % ret vol".format(inst)] \
    if historical_data[:date].tail(25)["{} active".format(inst)].all() else 0.025
#what is this? it says if the stock has been actively traded in the last 25 days for all days, then use the rolling volatility of
#stock returns. else use 2.5%. Why? Imagine if the stock is not active, trades like 1 1 1 1 2 1 1 1 1 2 1 1 1 , and barely moves
#being halted on most days. This would blow up the standard deviation, and if sizing is proportional to 1/std, then small std indicates position blows up
#this is a risk hazard.
"""