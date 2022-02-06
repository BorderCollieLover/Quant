#before that, let's integrate our backtesting and data pipeline into a brokerage.
#I just created an Oanda account.

#OANDA DOCUMENTATION: https://readthedocs.org/projects/oanda-api-v20/downloads/pdf/latest/
#oanda key: c10e84608f901cd434ce2ba9fe325f8b-52f63d26d5b95fb79a671693cf655c3a
#oanda id: 101-003-13732651-005

#ok, so we can read through the docs based on what we need
#we are going to go with the REST API option, instead of the streaming option

from brokerage.oanda.TradeClient import TradeClient
from brokerage.oanda.ServiceClient import ServiceClient

class Oanda():

    def __init__(self, brokerage_config={}, auth_config=""):
        self.trade_client = TradeClient(auth_config=auth_config)
        self.service_client = ServiceClient()

    def get_trade_client(self):
        return self.trade_client

    def get_service_client(self):
        return self.service_client
