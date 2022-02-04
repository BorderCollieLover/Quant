import datetime
import requests
import pandas as pd
import yfinance as yf

from bs4 import BeautifulSoup 

def get_sp500_instruments():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.content,'lxml')
    table = soup.find_all('table')[0] 
    df = pd.read_html(str(table))
    return list(df[0]["Symbol"])

def get_sp500_changes():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.content,'lxml')
    table = soup.find_all('table')[1] 
    df = pd.read_html(str(table))
    df = df[0]
    new_columns = list(map(lambda x : "{}".format(x[0]) if (x[0]==x[1]) else "{} {}".format(x[0],x[1]), df.columns))
    df.columns = new_columns
    return df
    

def get_hkex_securities():
    pass
    return


#now let's get its ohlcv data.
def get_sp500_df():
    symbols = get_sp500_instruments() #lets just do it for 30 stocks
    symbols = symbols[:30]
    ohlcvs = {}
    for symbol in symbols:
        symbol_df = yf.Ticker(symbol).history(period="10y")
        ohlcvs[symbol] = symbol_df[["Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"}
        )
    #lets create a single dataframe with all the data inside

    df = pd.DataFrame(index=ohlcvs["AMZN"].index)
    df.index.name = "date"
    instruments = list(ohlcvs.keys())

    for inst in instruments:
        inst_df = ohlcvs[inst]
        #add an identifier to the columns
        columns = list(map(lambda x: "{} {}".format(inst, x), inst_df.columns))
        #this adds the instrument name to each column
        df[columns] = inst_df

    return df, instruments

def extend_dataframe(traded, df):
    df.index = pd.Series(df.index).apply(lambda x: format_date(x))
    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))
    historical_data = df.copy()
    historical_data = historical_data[open_cols + high_cols + low_cols + close_cols + volume_cols]
    historical_data.fillna(method="ffill", inplace=True)
    for inst in traded:
        #lets get return statistics using closing prices
        #and volatility statistics using rolling standard deviations of 25 day window
        #lets also see if a stock is being actively traded, by seeing if closing price today != yesterday
        historical_data["{} % ret".format(inst)] = historical_data["{} close".format(inst)] \
            / historical_data["{} close".format(inst)].shift(1) - 1
        historical_data["{} % ret vol".format(inst)] = historical_data["{} % ret".format(inst)].rolling(25).std()
        historical_data["{} active".format(inst)] = historical_data["{} close".format(inst)] \
            != historical_data["{} close".format(inst)].shift(1)
    historical_data.fillna(method="bfill", inplace=True)
    return historical_data

#when obtaining data from numerous sources, we want to standardize communication units.
#in other words, we want our object types to be the same. for instance, things like
#dataframe index `type` or class should be the same.
def format_date(dates):
    yymmdd = list(map(lambda x: int(x), str(dates).split(" ")[0].split("-")))
    #what this does is take a list of dates in [yy--mm--dd {other stuff}] format
    #strips away the other stuff, then returns a datetime object
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])
    