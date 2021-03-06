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
    return df[0]


def get_sp500_changes():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.content,'lxml')
    table = soup.find_all('table')[1] 
    df = pd.read_html(str(table))
    df = df[0]
    new_columns = list(map(lambda x : "{}".format(x[0]) if (x[0]==x[1]) else "{} {}".format(x[0],x[1]), df.columns))
    df.columns = new_columns
    return df

def get_ndq_instruments():
    res = requests.get("https://en.wikipedia.org/wiki/Nasdaq-100")
    soup = BeautifulSoup(res.content,'lxml')
    table = soup.find_all('table')[3] 
    df = pd.read_html(str(table))
    return df[0]

    


#a generic function for retrieving data from Yahoo Finance
def get_yf_daily_ohlcv(symbol, period="max"):
    symbol_df = yf.Ticker(symbol).history(period=period)
    if not symbol_df.empty:
        symbol_df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "stocksplits"}
        , inplace=True)
        symbol_df.fillna(method="ffill", inplace=True)
        symbol_df.fillna(method="bfill", inplace=True)
    return symbol_df



#now let's get its ohlcv data.
def get_sp500_df():
    symbols = get_sp500_instruments() #lets just do it for 30 stocks
    symbols = symbols[:30]
    ohlcvs = {}
    for symbol in symbols:
        # symbol_df = yf.Ticker(symbol).history(period="max")
        # ohlcvs[symbol] = symbol_df[["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]].rename(
        #     columns={
        #         "Open": "open",
        #         "High": "high",
        #         "Low": "low",
        #         "Close": "close",
        #         "Volume": "volume",
        #         "Dividends": "dividends",
        #         "Stock Splits": "stocksplits"}
        # )
        ohlcvs[symbol] = get_yf_daily_ohlcv(symbol)
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



    

def extend_dataframe(traded, df, fx_codes):
    df.index = pd.Series(df.index).apply(lambda x: format_date(x))
    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))
    historical_data = df.copy()
    print(historical_data)
    historical_data = historical_data[open_cols + high_cols + low_cols + close_cols + volume_cols]
    historical_data.fillna(method="ffill", inplace=True)
    historical_data.fillna(method="bfill", inplace=True)
    for inst in traded:
        historical_data["{} % ret".format(inst)] = historical_data["{} close".format(inst)] \
            / historical_data["{} close".format(inst)].shift(1) - 1
        historical_data["{} % ret vol".format(inst)] = historical_data["{} % ret".format(inst)].rolling(25).std()
        historical_data["{} active".format(inst)] = historical_data["{} close".format(inst)] \
            != historical_data["{} close".format(inst)].shift(1)
        
        #also include the inverse fx quotes for simplicity in later fx calculations
        if is_fx(inst, fx_codes):
            inst_rev = "{}_{}".format(inst.split("_")[1], inst.split("_")[0])
            historical_data["{} close".format(inst_rev)] = 1 / historical_data["{} close".format(inst)]
            historical_data["{} % ret".format(inst_rev)] = historical_data["{} close".format(inst_rev)] \
                / historical_data["{} close".format(inst_rev)].shift(1) - 1
            historical_data["{} % ret vol".format(inst_rev)] = historical_data["{} % ret".format(inst_rev)].rolling(25).std()
            historical_data["{} active".format(inst_rev)] = historical_data["{} close".format(inst_rev)] \
                != historical_data["{} close".format(inst_rev)].shift(1)            
        
    return historical_data

def is_fx(inst, fx_codes):
    #e.g. EUR_USD, USD_SGD
    return len(inst.split("_")) == 2 and inst.split("_")[0] in fx_codes and inst.split("_")[1] in fx_codes 

#when obtaining data from numerous sources, we want to standardize communication units.
#in other words, we want our object types to be the same. for instance, things like
#dataframe index `type` or class should be the same.
def format_date(dates):
    yymmdd = list(map(lambda x: int(x), str(dates).split(" ")[0].split("-")))
    #what this does is take a list of dates in [yy--mm--dd {other stuff}] format
    #strips away the other stuff, then returns a datetime object
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])
    