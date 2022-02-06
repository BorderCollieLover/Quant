#in terms of the system implementation, both Oanda and Darwinex brokerages have been completed.
#in order to run different systems, all we have to do is change the settings in the master portfolio_config.json file
#we shall wrap up our discussion on multi-strat quant systems soon, and we will sum up some learnings throughout the course and
#give notes that we think are important.

#In order to implement your own strategies or brokerage, it should not be too difficult.
#To implement a new strategy
#1. Add the config files for your brokerages for the strategy
#2. Add the model to the main driver, Perform Calculation on the Strategy Model
#3. Adjust weight allocation if static

#To implement a new brokerage
#1. Implement the Trade and Service Client logic

#With that I would like to conclude the main demonstration for quant multi strat programming walk along. I hope you enjoyed it!
#I am looking forward to add on more material as we go along, and I will keep readers posted on Twitter and on the HangukQuant Newsletter!
#Goodbye!

#PUBLIC PACKAGES
import json
import pandas as pd
import datetime

#PRIVATE PACKAGES, local to environment
import quantlib.data_utils as du
import quantlib.general_utils as gu
import quantlib.backtest_utils as backtest_utils
import quantlib.diagnostics_utils as diagnostics_utils

#PUBLIC
from dateutil.relativedelta import relativedelta

#PRIVATE, LOCAL to project
from brokerage.oanda.oanda import Oanda
from brokerage.darwinex.darwinex import Darwinex
from subsystems.lbmom.subsys import Lbmom
from subsystems.lsmom.subsys import Lsmom
from subsystems.skprm.subsys import Skprm
from  quantlib.printer_utils import Printer
from quantlib.printer_utils import _Colors as Colors
from quantlib.printer_utils import _Highlights as Highlights

with open("config/auth_config.json") as f:
    auth_config = json.load(f)
with open("config/portfolio_config.json") as f:
    #master settings for the portfolio
    portfolio_config = json.load(f) 

brokerage_used = portfolio_config["brokerage"]
brokerage_config_path = portfolio_config["brokerage_config"][brokerage_used]
db_file = portfolio_config["database"][brokerage_used]
use_disk = portfolio_config["use_disk"]

with open("config/{}".format(brokerage_config_path)) as f:
    brokerage_config = json.load(f)

if brokerage_used == "oan":
    brokerage = Oanda(brokerage_config=brokerage_config, auth_config=auth_config)
    db_instruments = brokerage_config["currencies"] + brokerage_config["indices"] \
        + brokerage_config["commodities"] + brokerage_config["metals"] + brokerage_config["bonds"]
elif brokerage_used == "dwx":
    brokerage = Darwinex(brokerage_config=brokerage_config, auth_config=None)
    db_instruments = brokerage_config["fx"] + brokerage_config["equities"] + brokerage_config["commodities"]
else:
    print("brokerage not implemented: {}".format(brokerage_used))
    exit()

def print_inst_details(order_config, is_held, required_change=None, percent_change=None, is_overriden=None):
    color = Colors.YELLOW if not is_held else Colors.BLUE
    Printer.pretty(left="INSTRUMENT:", centre=order_config["instrument"], color=color)
    Printer.pretty(left="CONTRACT SIZE:", centre=order_config["contract_size"], color=color)
    Printer.pretty(left="OPTIMAL UNITS:", centre=order_config["scaled_units"], color=color)
    Printer.pretty(left="CURRENT UNITS:", centre=order_config["current_units"], color=color)
    Printer.pretty(left="OPTIMAL CONTRACTS:", centre=order_config["optimal_contracts"], color=color)
    Printer.pretty(left="OPTIMAL ROUNDED:", centre=order_config["rounded_contracts"], color=color)
    Printer.pretty(left="CURRENT CONTRACTS:", centre=order_config["current_contracts"], color=color)
    if not is_held:
        Printer.pretty(left="ORDER CHANGE:", centre=order_config["rounded_contracts"], color=Colors.WHITE)
    else:
        Printer.pretty(left="ORDER CHANGE:", centre=required_change, color=Colors.WHITE)
        Printer.pretty(left="% CHANGE:", centre=percent_change, color=Colors.WHITE)
        Printer.pretty(left="INERTIA OVERRIDE", centre=str(is_overriden), color=Colors.WHITE)

def print_order_details(contracts):
    Printer.pretty(left="MARKET ORDER", centre=str(contracts), color=Colors.RED)

def run_simulation(instruments, historical_data, portfolio_vol, subsystems_dict, subsystems_weights, brokerage_used, use_disk=False):
    """
    Init & Pre-processing
    """
    if use_disk:
        return  gu.load_file(
            "./backtests/{}_{}.obj".format(brokerage_used, "HANGUKQUANT")
        )
    
    test_ranges = []
    for subsystem in subsystems_dict.keys():
        test_ranges.append(subsystems_dict[subsystem]["strat_df"].index)
    start = max(test_ranges, key=lambda x:[0])[0]
    print(start)
    
    portfolio_df = pd.DataFrame(index=historical_data[start:].index).reset_index()
    portfolio_df.loc[0, "capital"] = 10000
    
    for i in portfolio_df.index:
        date = portfolio_df.loc[i, "date"]
        strat_scalar = 2

        """
        Get PnL and Scalar for Portfolio
        """
        if i != 0:
            date_prev = portfolio_df.loc[i - 1, "date"]
            pnl = backtest_utils.get_backtest_day_stats(\
                portfolio_df, instruments, date, date_prev, i, historical_data)
            strat_scalar = backtest_utils.get_strat_scaler(\
                portfolio_df, 100, portfolio_vol, i, strat_scalar)
        
        portfolio_df.loc[i, "strat scalar"] = strat_scalar

        """
        Get Positions for Traded Instruments, Assign 0 to Non-Traded
        """
        inst_units = {}
        for inst in instruments:
            inst_dict = {}
            for subsystem in subsystems_dict.keys():
                subdf = subsystems_dict[subsystem]["strat_df"]
                subunits = subdf.loc[date, "{} units".format(inst)] \
                    if "{} units".format(inst) in subdf.columns else 0
                subscalar = portfolio_df.loc[i, "capital"] / subdf.loc[date, "capital"] \
                    if date in subdf.index else 0 #scale up positions to match portfolio capital
                inst_dict[subsystem] = subunits * subscalar
            inst_units[inst] = inst_dict

        nominal_total = 0
        for inst in instruments:
            combined_sizing = 0
            for subsystem in subsystems_dict.keys():
                #signal/tactical alloation scheme determines the subsystems_weights dictionary values
                combined_sizing += inst_units[inst][subsystem] * subsystems_weights[subsystem]
            position = combined_sizing * strat_scalar #overall scalar to match portfolio vol target
            portfolio_df.loc[i, "{} units".format(inst)] = position
            if position != 0:
                nominal_total += abs(position * backtest_utils.unit_dollar_value(inst, historical_data, date))
    
        for inst in instruments:
            units = portfolio_df.loc[i, "{} units".format(inst)]
            if units != 0:
                nominal_inst = units * backtest_utils.unit_dollar_value(inst, historical_data, date)
                inst_w = nominal_inst / nominal_total
                portfolio_df.loc[i, "{} w".format(inst)] = inst_w
            else:
                portfolio_df.loc[i, "{} w".format(inst)] = 0
        
        nominal_total = backtest_utils.set_leverage_cap(
            portfolio_df, instruments, date, i, nominal_total, 5, historical_data)
        
        portfolio_df.loc[i, "nominal"] = nominal_total
        portfolio_df.loc[i, "leverage"] = portfolio_df.loc[i, "nominal"] / portfolio_df.loc[i, "capital"]
        print(portfolio_df.loc[i])
    
    portfolio_df.set_index("date", inplace=True)    

    diagnostics_utils.save_backtests(
        portfolio_df=portfolio_df,
        instruments=instruments,
        brokerage_used=brokerage_used,
        sysname="HANGUKQUANT"
    )
    diagnostics_utils.save_diagnostics(
        portfolio_df=portfolio_df,
        instruments=instruments,
        brokerage_used=brokerage_used,
        sysname="HANGUKQUANT"
    )
    return portfolio_df

def reset_df():
    poll_df = pd.DataFrame()
    for db_inst in db_instruments:
        tries = 0
        again = True
        while again:
            try:
                print(db_inst)
                df = brokerage.get_trade_client().get_ohlcv(instrument=db_inst, count=7000, granularity="D")\
                    .set_index("date")
                cols = list(map(lambda x: "{} {}".format(db_inst, x), df.columns))
                df.columns = cols
                if len(poll_df) == 0:
                    poll_df[cols] = df
                else:
                    poll_df = poll_df.combine_first(df) 
                again=False
            except Exception as err:
                tries += 1
                if tries >= 5:
                    again = False
                    print("{} CHECK CONNECTION TO BROKERAGE, RESTART APP: {}".format(db_inst, str(err)))
                    exit()
                print("polling {} again from brokerage".format(db_inst))
    poll_df.to_excel("./Data/{}".format(db_file))
    print("new df set")
    exit()

def main():
    """
    Load and Update Database
    """
    database_df = pd.read_excel("./Data/{}".format(db_file)).set_index("date")
    database_df = database_df.loc[~database_df.index.duplicated()]
    print(database_df)

    if not use_disk:
        poll_df = pd.DataFrame()
        for db_inst in db_instruments:
            tries = 0
            again = True
            while again:
                try:
                    print(db_inst)
                    df = brokerage.get_trade_client().get_ohlcv(instrument=db_inst, count=30, granularity="D")\
                        .set_index("date")
                    cols = list(map(lambda x: "{} {}".format(db_inst, x), df.columns))
                    df.columns = cols
                    if len(poll_df) == 0:
                        poll_df[cols] = df
                    else:
                        poll_df = poll_df.combine_first(df) 
                    again=False
                except Exception as err:
                    tries += 1
                    if tries >= 5:
                        again = False
                        print("{} CHECK CONNECTION TO BROKERAGE, RESTART APP: {}".format(db_inst, str(err)))
                        exit()
                    print("polling {} again from brokerage".format(db_inst))

        database_df = database_df.loc[:poll_df.index[0]][:-1]
        database_df = database_df.append(poll_df)
        database_df.to_excel("./Data/{}".format(db_file))
    
    """
    Extend dataframe with numerical statistics required for backtesting and alpha generation
    """
    historical_data = du.extend_dataframe(\
        traded=db_instruments, df=database_df, fx_codes=brokerage_config["fx_codes"])
    
    """
    Risk Parameters
    """
    vol_target = portfolio_config["vol_target"]
    sim_start = datetime.date.today() - relativedelta(years=portfolio_config["sim_years"])
    
    """
    Get Existing Positions, Capital etc.
    """
    capital = brokerage.get_trade_client().get_account_capital()
    positions = brokerage.get_trade_client().get_account_positions()
    print(capital, positions) #our netted positions are shown
    
    """
    Subystem Positioning
    """
    subsystems_config = portfolio_config["subsystems"][brokerage_used]
    strats = {}

    for subsystem in subsystems_config.keys():
        if subsystem == "lbmom":
            strat = Lbmom(
                instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used], \
                historical_df=historical_data, 
                simulation_start=sim_start, 
                vol_target=vol_target,
                brokerage_used=brokerage_used
            )
        elif subsystem == "lsmom":
            strat = Lsmom(
                instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used], \
                historical_df=historical_data, 
                simulation_start=sim_start, 
                vol_target=vol_target,
                brokerage_used=brokerage_used
            )
        elif subsystem == "skprm":
            strat = Skprm(
                instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used], \
                historical_df=historical_data, 
                simulation_start=sim_start, 
                vol_target=vol_target,
                brokerage_used=brokerage_used
            )
        else:
            print("unknown strat: ", subsystem)
            exit()

        strats[subsystem] = strat
    
    subsystems_dict = {}
    traded = []
    for k, v in strats.items():
        strat_df, strat_inst = v.get_subsys_pos(debug=True, use_disk=use_disk)
        print(strat_df, strat_inst)
        subsystems_dict[k] = {
            "strat_df": strat_df,
            "strat_inst": strat_inst
        }
        traded += strat_inst
 
    traded = list(set(traded))
    
    portfolio_df = run_simulation(
        instruments=traded, 
        historical_data=historical_data, 
        portfolio_vol=vol_target, 
        subsystems_dict=subsystems_dict, 
        subsystems_weights=subsystems_config,
        brokerage_used=brokerage_used,
        use_disk=use_disk
    )    
    
    """
    Live Optimal Portfolio Allocations
    """
    trade_on_date = portfolio_df.index[-1] #last updated data point
    capital_scalar = capital / portfolio_df.loc[trade_on_date, "capital"]
    portfolio_optimal = {}
    for inst in traded:
        unscaled_optimal = portfolio_df.loc[trade_on_date, "{} units".format(inst)]
        scaled_units = unscaled_optimal * capital_scalar
        portfolio_optimal[inst] = {
            "unscaled": unscaled_optimal,
            "scaled_units": scaled_units,
            "rounded_units": round(scaled_units),
            "nominal_exposure": abs(scaled_units * backtest_utils.unit_dollar_value(
                inst, historical_data, trade_on_date
            )) if scaled_units != 0 else 0
        }

    instruments_held = positions.keys()
    instruments_unheld = [inst for inst in traded if inst not in instruments_held]

    input("MARKET ORDERS: PRESS ANYTHING TO CONTINUE")

    """
    Edit Open Positions
    """
    for inst_held in instruments_held:
        Printer.pretty(left="\n*****************************************************", color=Colors.BLUE)
        order_config = brokerage.get_service_client().get_order_specs(
            inst=inst_held,
            scaled_units=portfolio_optimal[inst_held]["scaled_units"],
            current_contracts=float(positions[inst_held])
        )
        required_change = round(order_config["rounded_contracts"] - order_config["current_contracts"], 2)
        percent_change = round(abs(required_change / order_config["current_contracts"]), 3)
        is_inertia_overriden = brokerage.get_service_client().is_inertia_overriden(percent_change)
        print_inst_details(\
            order_config, True, required_change=required_change, 
            percent_change=percent_change, is_overriden=is_inertia_overriden
        )

        if is_inertia_overriden:
            print_order_details(required_change)
            if portfolio_config["order_enabled"]:
                brokerage.get_trade_client().market_order(
                    inst=inst_held,
                    order_config=order_config
                )      
        Printer.pretty(left="*****************************************************\n", color=Colors.BLUE)

    """
    Open New Positions
    """
    for inst_unheld in instruments_unheld:
        Printer.pretty(left="\n*****************************************************", color=Colors.YELLOW)
        order_config = brokerage.get_service_client().get_order_specs(
            inst=inst_unheld,
            scaled_units=portfolio_optimal[inst_unheld]["scaled_units"],
            current_contracts=0
        )
        if order_config["rounded_contracts"] != 0:
            print_inst_details(order_config, False)
            print_order_details(order_config["rounded_contracts"])
            if portfolio_config["order_enabled"]:
                brokerage.get_trade_client().market_order(
                    inst=inst_unheld,
                    order_config=order_config
                )
        Printer.pretty(left="*****************************************************\n", color=Colors.YELLOW)

if __name__ == "__main__":
    main()
