import json
import pandas as pd

import quantlib.indicators_cal as indicators_cal

"""
https://hangukquant.substack.com/p/volatility-targeting-the-asset-level
https://hangukquant.substack.com/p/volatility-targeting-the-strategy
"""

class Lbmom():

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target):
        self.pairs = [(23, 82), (44, 244), (124, 294), (37, 229), (70, 269), (158, 209), (81, 169), (184, 203), (23, 265), (244, 268), (105, 106), (193, 250), (127, 294), (217, 274), (45, 178), (103, 288), (204, 248), (142, 299), (71, 216), (129, 148), (149, 218)]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target #for more information on volatility targetting, refer to my post linked
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)
        self.sysname = "LBMOM"

    #we implement a few functions
    #1. A function to get extra indicators specific to this strategy
    #2. A function to run a backtest/get positions from this strategy

    def extend_historicals(self, instruments, historical_data):
        #we need indicators of `momentum`
        #let this be the moving average crossover, such that if the fastMA crossover the slowMA, then it is a buy
        #a long-biased momentum strategy is biased in the long direction. let this be a 100/0 L/S strategy.
        #let's also use a filter, to identify false positive signals. We use the average directional index, or the adx

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
                ) #fastMA - slowMA
        #now historical data has ohlcvs, and whether the fastMA - slowMA for each pair, 
        #and the adx of the closing prices to see if there is a `trending` regime
        return historical_data    
    
    def run_simulation(self, historical_data):
        #init parameters
        instruments = self.instruments_config["instruments"]
        
        #calculate/pre-process indicators
        historical_data = self.extend_historicals(instruments=instruments, historical_data=historical_data)

        #perform simulation
        portfolio_df = pd.DataFrame(index=historical_data[self.simulation_start:].index).reset_index()
        print(portfolio_df)

        #run diagnostics

        #return dataframe
        pass

    def get_subsys_pos(self):
        self.run_simulation(historical_data=self.historical_df)


#now, from our main driver, we pass the dataframe into the LBMOM strategy, than let the LBMOM perform some 
#calculations using the quantlib indicators calculator.
#after the calculations, we pass into the simulator, where we can run some simulations and backtesting!

#we covered some sound principles to make sure the logic is passed around, in flexible fashion.
#we don't perform unnecssary calculations - we do general calc in the driver, such as returns, volatility etc
#needed for all strats. then, indicators specific to strat is done inside the strategy to save time.

#each strategy has a config file, so that we can control some parameters. later, we shall see how this might be useful
#:)))

#ok break.
