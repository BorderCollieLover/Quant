import numpy as np
import pandas as pd

def get_backtest_day_stats(portfolio_df, instruments, date, date_prev, date_idx, historical_data):
    day_pnl = 0
    nominal_ret = 0
    for inst in instruments:
        previous_holdings = portfolio_df.loc[date_idx - 1, "{} units".format(inst)]
        if previous_holdings != 0:
            price_change = historical_data.loc[date, "{} close".format(inst)] - \
                historical_data.loc[date_prev, "{} close".format(inst)]
            dollar_change = unit_val_change(
                from_prod=inst,
                val_change=price_change,
                historical_data=historical_data,
                date=date_prev
            )
            inst_pnl = dollar_change * previous_holdings
            day_pnl += inst_pnl
            nominal_ret += portfolio_df.loc[date_idx - 1, "{} w".format(inst)] * \
                historical_data.loc[date, "{} % ret".format(inst)]

    capital_ret = nominal_ret * portfolio_df.loc[date_idx - 1, "leverage"]
    portfolio_df.loc[date_idx, "capital"] = portfolio_df.loc[date_idx - 1, "capital"] + day_pnl
    portfolio_df.loc[date_idx, "daily pnl"] = day_pnl
    portfolio_df.loc[date_idx, "nominal ret"] = nominal_ret
    portfolio_df.loc[date_idx, "capital ret"] = capital_ret
    return day_pnl

def get_strat_scaler(portfolio_df, lookback, vol_target, idx, default):
    capital_ret_history = portfolio_df.loc[:idx].dropna().tail(lookback)["capital ret"]
    strat_scaler_history = portfolio_df.loc[:idx].dropna().tail(lookback)["strat scalar"]
    if len(capital_ret_history) == lookback: #enough data
        annualized_vol = capital_ret_history.std() * np.sqrt(253)
        scalar_hist_avg = np.mean(strat_scaler_history)
        strat_scalar = scalar_hist_avg * vol_target / annualized_vol
        return strat_scalar
    else:
        return default

def unit_val_change(from_prod, val_change, historical_data, date):
    is_denominated = len(from_prod.split("_")) == 2
    if not is_denominated:
        return val_change
    elif is_denominated and from_prod.split("_")[1] == "USD":
        return val_change
    else:
        return val_change * historical_data.loc[date, "{}_USD close".format(from_prod.split("_")[1])]

#the contract dollar value in base currency of the from_prod
def unit_dollar_value(from_prod, historical_data, date):
    is_denominated = len(from_prod.split("_")) == 2 
    if not is_denominated: #e.g. AAPL, GOOGL: 1 contract of AAPL is worth the price of AAPL
        return historical_data.loc[date, from_prod + " close"]
    if is_denominated and from_prod.split("_")[0] == "USD": #e.g. USD_JPY, USD_MXN
        #the good, or the thing that is being bought is 1 unit of USD. therefore one unit is worth 1 USD
        return 1
    if is_denominated and not from_prod.split("_")[0] == "USD": 
        #HK33_HKD. one contract is worth that price in HKD, convert OR
        #EUR_USD etc
        #so x_y means one contract of x in y dollars.
        #so in USD terms, the dollar value of the contract is x * y_USD
        #i.e. HK33_HKD = 5HKD
        #in dollar terms, 5HKD * HKD/USD
        #i.e. EUR/USD = x >> x * USD/USD = x
        #i.e. EUR/HKD = x >> x * HKD/USD
        unit_price = historical_data.loc[date, from_prod + " close"]
        fx_inst = "{}_{}".format(from_prod.split("_")[1], "USD")
        fx_quote = 1 if fx_inst == "USD_USD" else historical_data.loc[date, fx_inst + " close"]
        return unit_price * fx_quote

def set_leverage_cap(portfolio_df, instruments, date, idx, nominal_tot, leverage_cap, historical_data):
    leverage = nominal_tot / portfolio_df.loc[idx, "capital"]
    if leverage > leverage_cap:
        new_nominals = 0
        leverage_scalar = leverage_cap / leverage
        for inst in instruments:
            newpos = portfolio_df.loc[idx, "{} units".format(inst)] * leverage_scalar
            portfolio_df.loc[idx, "{} units".format(inst)] = newpos
            if newpos != 0:
                new_nominals += abs(newpos * unit_dollar_value(inst, historical_data, date))
        return new_nominals
    else:
        return nominal_tot

#get some summary statistics of the strategy
def kpis(df):
    portfolio_df = df.copy()
    portfolio_df["cum ret"] = (1 + portfolio_df["capital ret"]).cumprod()
    portfolio_df["drawdown"] = portfolio_df["cum ret"] / portfolio_df["cum ret"].cummax() - 1
    sharpe = portfolio_df["capital ret"].mean() / portfolio_df["capital ret"].std() * np.sqrt(253)
    drawdown_max = portfolio_df["drawdown"].min() * 100
    volatility = portfolio_df["capital ret"].std() * np.sqrt(253) * 100
    return portfolio_df, sharpe, drawdown_max, volatility
