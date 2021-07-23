import pandas as pd
from Position import Order, Position
from typing import Dict, List, Optional, Tuple
from Market import Market
from scipy.signal import argrelextrema
import numpy as np
from strategy_config import EMA_INTERVAL, PRICE_RANGE_CHECKED
from enum import Enum


Trade = Tuple[Order, Position]
Time = str
Price = int
Weight = int # datapoint importance
Market_name = str
Datapoint = str
EMA_data = pd.DataFrame

class Trend(Enum):
    UP = 0
    DOWN = 1
    CONSOLIDATION = 2

class Strategy:

    markets_EMAs: Dict[Market_name, EMA_data] = dict()
    market_last_check: Dict[Market_name, Time] = dict()

    def __init__(self,watched_markets: Dict[str, Market]) -> None:
        for market in watched_markets.values():
            self.analyze_price_action(market)

    def evaluate_market(self, market: Market) -> Optional[Trade]:
        ''' 
        Returns possible Trade for given market,
        consiting of Order and Position. 
        Order triggers given Position. 
        '''
        self.update_analysis(market)
        if not market.has_active_position():
            return self.check_for_position()
        pass # TODO: switching positions if EMA cross occured
             #       | setting market SL and TP (dont know about the TP with this strategy for now)
             #       | setting market order for position trigger
             #       | creating position specification
        
    def check_for_position(self) -> Optional[Trade]:
        pass # TODO: palce position if cross of EMA occured on
             #       last candle and if price is close enough to EMA

    def analyze_price_action(self, market: Market, start_time: str = None) -> None:
        last_EMA = market.price_data['close'].loc[0:20].sum(axis=0) / EMA_INTERVAL if start_time is None else \
            self.markets_EMAs[market.name].tail(1).iloc[0,0]

        # este bude treba pocas nacitania v main classe zmenit startTimes na datetime objekty
        relevant_candles = market.price_data.loc[20:] if start_time is None else \
            market.price_data.loc[market.price_data['startTime'] > start_time]

        market_EMAs = {
            'startTime': [],
            'EMA': []
        }


        for _, row in relevant_candles.iterrows():
            close = row['close']
            time = row['startTime']
            last_EMA = (2 / (EMA_INTERVAL + 1)) * (close - last_EMA) + last_EMA
            market_EMAs['startTime'].append(time)
            market_EMAs['EMA'].append(last_EMA)
        
        self.markets_EMAs[market.name] = pd.DataFrame(market_EMAs)
        self.market_last_check[market.name] = market_EMAs['startTime'][-1]

    def update_analysis(self, market: Market) -> None:
        last_historical_price = market.price_data.tail(1).iloc[0,0]
        if last_historical_price != self.market_last_check[market.name]:
            self.analyze_price_action(market, self.market_last_check[market.name])



        