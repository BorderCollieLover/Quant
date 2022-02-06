#Introduction and Tutorial Series on PUSH/PULL ARCHITECTURE, ZEROMQ: https://www.youtube.com/watch?v=GGOajzvl860
#Darwinex Tutorial Series on MT4 and Python Interfacing
#Repo name: https://github.com/darwinex/dwx-zeromq-connector
#MT4 Setup: https://www.youtube.com/watch?v=N0-aYLllK3E
#https://docs.mql4.com/constants/environment_state/accountinformation

#it seems that darwinex has given us the functions to download prices, submit trades and get open trades.
#we still need to be able to get account details, such as the amount of capital etc.
#let's implement that functionality, and then we can code a service and a trade client wrapper for the dwx mt4 connector

#We chose the brokerage to be Darwinex. Based on what I see, they have many different platforms and different 
#tech stacks. This includes (REST API *what oanda uses, FIX API, and also have MT4 platforms which I understand
# to be popular) We will be interfacing our Python quantbot with an open MT4 terminal using a communication protocol
#called the TCP protocol which lies on the transport layer of an OSI model.

#https://www.darwinex.com/spreads/indices
#shows us the margin requirements, contract sizing for the different instruments etc
#again, we can either scrape this, or copy.

from brokerage.darwinex.TradeClient import TradeClient
from brokerage.darwinex.ServiceClient import ServiceClient

class Darwinex():

    def __init__(self, brokerage_config=None, auth_config=None):
        self.brokerage_config=brokerage_config
        self.auth_config=auth_config
        self.trade_client = None
        self.service_client = None

    def get_trade_client(self):
        if self.trade_client is None:
            self.trade_client = TradeClient(
                brokerage_config=self.brokerage_config,
                auth_config=self.auth_config,
                service_client=self.get_service_client()
            )
        return self.trade_client

    def get_service_client(self):
        if self.service_client is None:
            self.service_client = ServiceClient(
                brokerage_config=self.brokerage_config
            )
        return self.service_client