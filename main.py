import quantlib.data_utils as du
import quantlib.general_utils as gu

from dateutil.relativedelta import relativedelta

from subsystems.lbmom.subsys import Lbmom

# df, instruments = du.get_sp500_df()
# df = du.extend_dataframe(traded=instruments, df=df)

(df, instruments) = gu.load_file("./Data/historical_df.obj")
print(instruments)

#lets run the lbmom strategy through the driver.

VOL_TARGET = 0.20 #we are targetting 20% annualized vol

#let's perform the simulation for the past 5 years

print(df.index[-1]) #is today's date. (as I film) 2022-01-19
#I want to start testing from 5 years back

sim_start = df.index[-1] - relativedelta(years=5)
print(sim_start) #2017-01-19

strat = Lbmom(instruments_config="./subsystems/lbmom/config.json", historical_df=df, \
    simulation_start=sim_start, vol_target=VOL_TARGET)

strat.get_subsys_pos()