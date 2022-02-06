import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import quantlib.general_utils as gu
from quantlib.backtest_utils import kpis


def save_backtests(portfolio_df, instruments, brokerage_used, sysname, path="./backtests/"):
    portfolio_df, sharpe, drawdown_max, vol_ann = kpis(df=portfolio_df)
    annotation = "{}: \nSharpe: {} \nDrawdown: {}\nVolatilty: {}\n".format(
        sysname, round(sharpe, 2), round(drawdown_max, 2), round(vol_ann, 2)
    )
    #plot log returns or cumulative returns
    ax = sns.lineplot(data=portfolio_df["cum ret"], linewidth=2.5, palette="deep")    
    ax.annotate(
        annotation, xy=(0.2, 0.8), xycoords="axes fraction", \
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.3),
        ha="center", va="center", family="serif", size="8.6"
    )
    plt.title("Cumulative Returns")
    plt.savefig("{}{}_{}.png".format(path, brokerage_used, sysname), bbox_inches="tight")
    plt.close()
    portfolio_df.to_excel("{}{}_{}.xlsx".format(path, brokerage_used, sysname))    
    gu.save_file("{}{}_{}.obj".format(path, brokerage_used, sysname), portfolio_df)    
    
#ok anyway, lets get some more diagnostics

def save_diagnostics(portfolio_df, instruments, brokerage_used, sysname, path="./diagnostics/"):
    #save signal allocations
    path += "{}/".format(sysname)
    for inst in instruments:
        portfolio_df["{} w".format(inst)].plot()
    plt.title("Instrument Weights")
    plt.savefig("{}{}_weights.png".format(path, brokerage_used), bbox_inches="tight")
    plt.close()

    #save leverage
    portfolio_df["leverage"].plot()
    plt.title("Portfolio Leverage")
    plt.savefig("{}{}_leverage.png".format(path, brokerage_used), bbox_inches="tight")
    plt.close()

    #scatter plot
    plt.scatter(portfolio_df.index, portfolio_df["capital ret"] * 100)
    plt.title("Return Scatter Plot")
    plt.savefig("{}{}_scatter.png".format(path, brokerage_used), bbox_inches="tight")
    plt.close()

    #and anything else