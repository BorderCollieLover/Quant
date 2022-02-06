import time
import json
import heapq
import datetime
import pandas as pd

from collections import defaultdict
from decimal import Decimal #helps with floating point precision and string arithmetic operations
from dateutil.relativedelta import relativedelta

from brokerage.darwinex.DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector

class TradeClient():

    def __init__(self, brokerage_config=None, auth_config=None, service_client=None):
        self.dwx_config = brokerage_config
        self._zmqclient = DWX_ZeroMQ_Connector(
            _PUSH_PORT=brokerage_config["ports"]["push"],
            _PULL_PORT=brokerage_config["ports"]["pull"],
            _SUB_PORT=brokerage_config["ports"]["sub"],
            _verbose=False
        )
        self.service_client = service_client


    def _request_result(self, s_delay=0.3):
        #recall that our data is passed through a TCP socket, and we may need to
        #wait for data to come in
        #once retrieving data, we also want to clear the _thread_data_output
        time.sleep(s_delay)
        res = self._zmqclient._thread_data_output
        self._zmqclient._thread_data_output = None
        return res

    def get_account_details(self):
        try:
            self._zmqclient._DWX_GET_ACCOUNT_DETAILS()
            res = self._request_result()
            return dict(res)
        except Exception as err:
            pass

    def get_account_summary(self):
        try:
            #this is the same as account_details
            return self.get_account_details()
        except Exception as err:
            raise Exception("some err message from acc summary: {}".format(str(err)))

    def get_account_capital(self):
        try:
            return float(self.get_account_summary()["_equity"])
        except Exception as err:
            pass

    def get_account_positions(self):
        trades = self.get_account_trades()
        positions = defaultdict(Decimal)
        for id in trades.keys():
            details = trades[id]
            if len(details) != 0:
                instrument = self.service_client.code_to_label_nomenclature(details["_symbol"])
                lots = Decimal(str(details["_lots"]))
                multiplier = 1 if details["_type"] == 0 else -1
                positions[instrument] += Decimal(str(lots * multiplier))
                #lets have an opposing position, now should be 0.07:: Unlike Oanda, there is no netting effect, the net position is 0.07 but there are
                #2 existing open orders that have to be closed to be net zero
        return positions

    def get_account_trades(self):
        client = self._zmqclient
        client._DWX_MTX_GET_ALL_OPEN_TRADES_()
        res = self._request_result(1)
        trades = dict(res)["_trades"]
        return trades

    def is_tradable(self, inst):
        try:
            return True 
        except Exception as err:
            print(err)

    def format_date(self, series):
        ddmmyy = series.split(" ")[0].split(".")
        return datetime.date(int(ddmmyy[0]), int(ddmmyy[1]), int(ddmmyy[2]))
    
    def get_ohlcv(self, instrument, count, granularity):
        try:
            client = self._zmqclient
            start = datetime.date.today()
            end = start - relativedelta(days=count)
            start = start.strftime("%Y/%m.%d %H:%M:00")
            end = end.strftime("%Y/%m.%d %H:%M:00")
            client._DWX_MTX_SEND_HIST_REQUEST_(
                _symbol=self.service_client.label_to_code_nomenclature(label=instrument),
                _start=start,
                _end=end
            )
            res = self._request_result()
            return_instrument = res["_symbol"].split("_")[0] if res["_symbol"].split("_")[1] == "D1" else None
            if return_instrument == self.service_client.label_to_code_nomenclature(label=instrument):
                ohlcv = pd.DataFrame(res["_data"])
                ohlcv["time"] = ohlcv["time"].apply(lambda x: self.format_date(x))
                ohlcv.drop(columns=["spread", "real_volume"], inplace=True)
                ohlcv.columns = ["date", "open", "high", "low", "close", "volume"]
                ohlcv.set_index("date", inplace=True)
                ohlcv = ohlcv.loc[~ohlcv.index.duplicated()]
                ohlcv = ohlcv.apply(pd.to_numeric)
                ohlcv.reset_index(inplace=True)
            return ohlcv
        except Exception as err:
            raise ConnectionError("ERROR: CANNOT GET OHLCV for {} : {}".format(instrument, str(err)))
    
    def _new_market_order(self, inst, contract_change): #market order on clean positions
        trade = self._get_market_order_dict(inst, contract_change)
        print(json.dumps(trade, indent=4))
        self._zmqclient._DWX_MTX_NEW_TRADE_(_order=(trade))
        res = self._request_result(1)
        print(res)
        return res
    
    def _get_market_order_dict(self, inst, contracts):
        return {
            '_action': 'OPEN',
            '_type': 0 if contracts > 0 else 1,
            '_symbol': self.service_client.label_to_code_nomenclature(inst),
            '_price': 0.0, #price taker
            '_SL': 0, # SL/TP in POINTS, not pips.
            '_TP': 0,
            '_comment': "HANGUKQUANT ORDER",
            '_lots': abs(contracts),
            '_magic': 123456,
            '_ticket': 0
        }

    #_ underscore in front of functions suggest that the method is not public facing, and that it is just a `helper` private function for DWX
    def _get_trades_stack(self, open_trades, inst):
        long_stack = []
        short_stack = []
        for id in open_trades.keys():
            details = open_trades[id]
            if len(details) != 0:
                instrument = self.service_client.code_to_label_nomenclature(details["_symbol"])
                if inst == instrument:
                    contracts = details["_lots"]
                    if details["_type"] == 0:
                        heapq.heappush(long_stack, (contracts, id))  #(key min sort, ticket_id)
                    elif details["_type"] == 1:
                        heapq.heappush(short_stack, (contracts, id))  
                    else:
                        print("Market Order Type Should be 0 or 1")
                        exit()          
        return long_stack, short_stack        

    def _adjust_order_market(self, inst, contract_change, long_stack, short_stack, is_long):
        #ok so here we want to reduce positions or close positions and open opposite directional trade
        client = self._zmqclient
        if (is_long and short_stack and not long_stack):
            #reduce short positions and get relatively longer
            while short_stack and contract_change > 0: #while existing short positions exist and we want to get longer
                smallest_short, ticket_id = heapq.heappop(short_stack)
                if smallest_short > contract_change: #then just shave from the smallest short
                    #close partial _DWX_MTX_CLOSE_PARTIAL_BY_TICKET_(self, _ticket, _lots):
                    client._DWX_MTX_CLOSE_PARTIAL_BY_TICKET_(_ticket=ticket_id, _lots=abs(round(contract_change, 2)))
                    res = self._request_result(1) #we just assign more waiting time on sensitive operations for tcp socket reply
                    contract_change = 0
                elif smallest_short <= contract_change:
                    #close smallest short and re-analyze the stack
                    client._DWX_MTX_CLOSE_TRADE_BY_TICKET_(_ticket=ticket_id)
                    res = self._request_result(1)
                    contract_change -= smallest_short #i.e. if we want contract_change = +10, we close short_position of size 3, then we left 7
            
            if contract_change < 0:
                raise Exception("Market Order Logic WRONG") #means we overshot
            elif contract_change > 0 and not short_stack: #means we want to go from net short to net long
                res = self._new_market_order(inst, contract_change)

        elif (not is_long and long_stack and not short_stack):
            while long_stack and contract_change < 0:
                smallest_long, ticket_id = heapq.heappop(long_stack)
                if smallest_long > abs(contract_change):
                    client._DWX_MTX_CLOSE_PARTIAL_BY_TICKET_(_ticket=ticket_id, _lots=abs(round(contract_change, 2)))
                    res = self._request_result(1)
                    contract_change = 0
                elif smallest_long <= abs(contract_change):
                    client._DWX_MTX_CLOSE_TRADE_BY_TICKET_(_ticket=ticket_id)
                    res = self._request_result(1)
                    contract_change += smallest_long             
            if contract_change > 0:
                raise Exception("Market Order Logic WRONG") 
            elif contract_change < 0 and not long_stack:
                res = self._new_market_order(inst, contract_change)

        return res
           
    def market_order(self, inst, order_config={}): #market order on any positions
        #it is not economically sensible to have 2 open order with cancelling effects, since we can obtain the same market exposure with less
        #trasnsaction costs, therefore saving our PnL
        #1. We will hence perform logic checks that all trades in a position are in the same direction (long or short) and there are no opposing ones
        #2. It will also be messy to have a large position with many many small orders. So when reducing net exposure to an asset, we will shave positions
        #   the smallest orders first, such that the smallest open trades are closed first. For instance suppose our AAPL position is 10 + 5 + 3 + 1,
        #   and we want to have net exposure of 11, we will close partially the 5, and fully the 3 + 1 to obtain 10 + 1.
        #Note: we can achieve 2 with a stack data structure, where the largest position is pushed first, and we pop the top of the stack to net positions
        client = self._zmqclient
        is_new = order_config["current_contracts"] == 0
        contract_change = round(order_config["rounded_contracts"] - order_config["current_contracts"], 2)
        is_long = contract_change > 0
        if is_new:
            print("OPEN NEW TRADES")
            res = self._new_market_order(inst, contract_change)
            return res
        else:
            open_trades = self.get_account_trades()
            long_stack, short_stack = self._get_trades_stack(open_trades, inst)
            if (not long_stack and not short_stack) or (long_stack and short_stack):
                raise Exception("Trade Stacks on Account is Invalid, Close Opposing Trades")
            if (is_long and long_stack and not short_stack) or (not is_long and short_stack and not long_stack):
                #means add to current directional view
                #do a market order and add to existing position
                print("ACCUMULATE EXISTING TRADE")
                res = self._new_market_order(inst, contract_change)
                return res
            elif (is_long and short_stack and not long_stack) or (not is_long and long_stack and not short_stack):
                #means reduce current open position, and possible even reverse directional view if magnitude of change exceeds current position
                #do a market order adjust
                print("REDUCE/OPPOSITE ON EXISTING TRADE")
                res = self._adjust_order_market(inst, contract_change, long_stack, short_stack, is_long)
                return res
            else:
                raise Exception("Unknown Trade Stack Configuration")