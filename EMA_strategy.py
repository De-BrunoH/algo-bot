import pandas as pd
from Position import Position
from datetime import timedelta
from Market import Market
from typing import Dict, List, Optional, Tuple
from trader_config import EMA_INTERVAL, Market_name, Stop_loss, Take_profit, EMA_data, Time, Todos, Trade

class EMA_strategy:
    update_checkpoint = timedelta(minutes=15)
    markets_EMA: Dict[Market_name, pd.DataFrame] = dict()
    market_last_check: Dict[Market_name, Time] = dict()

    def __init__(self, markets: List[Market_name]) -> None:
        for market_name in markets:
            self.markets_EMA[market_name] = []
            self.market_last_check[market_name] = None

    def recog_orders(self, orders: List[dict]) -> Tuple[Stop_loss, List[Take_profit]]:
        '''
        Sorts existing orders in order: Stop_loss, List[Take_profit]
        Works only for Strategy that uses 1 position (therefore many TP and exactly 1 SL order )
        '''
        if not orders:
            return None, None
        Sl_orders = []
        Tp_orders = []
        for order in orders:
            if order['type'] == 'stop' or order['type'] == 'trailingStop':
                Sl_orders.append(order)
            else:
                Tp_orders.append(order)
        return Sl_orders, Tp_orders

    def evaluate_market(self, market: Market) -> List[Todos]:
        self.calculate_EMA(market)
        todos = self.evaluate_price_action(market)
        self.last_process_time = self.markets_EMA[market.name][-1][0]
        return todos

    def calculate_EMA(self, market: Market) -> None:
        last_check = self.market_last_check[market.name]
        last_EMA = market.price_data['close'].loc[0:EMA_INTERVAL - 1].sum(axis=0) / EMA_INTERVAL if last_check is None \
            else self.markets_EMAs[market.name][-1][1]

        relevant_candles = market.price_data.loc[20:] if last_check is None else \
            market.price_data.loc[market.price_data['time'] > last_check]

        market_EMAs = {
            'time': [],
            'EMA': []
        }

        for _, row in relevant_candles.iterrows():
            close = row['close']
            time = row['time']
            last_EMA = (2 / (EMA_INTERVAL + 1)) * (close - last_EMA) + last_EMA
            market_EMAs['time'].append(time)
            market_EMAs['EMA'].append(last_EMA)
        
        self.markets_EMAs[market.name] = pd.DataFrame(market_EMAs)
        self.market_last_check[market.name] = market_EMAs['startTime'][-1]

    def difference_price_EMA(self, market: Market) -> float:
        return market.price_data['close'].tail(1).iloc[0,0] - self.markets_EMA[market.name]['EMA'].tail(1).iloc[0,0]

    def position_is_switchable(self, market: Market, price_EMA_diff: float) -> bool:
        ''' Returns if position can be opened immediately 
            after the close on the other side of market.
        '''
        pass

    def position_is_closable(self, market: Market, price_EMA_diff: float) -> bool:
        ''' Returns if position can be closed according to rules:
            if current price is in acceptable range from EMA.
        '''
        pass

    def create_position(self, market: Market, side: str , price_EMA_diff: float) -> Position:
        ''' Creates new position on market side according to rules.
            Sets SL and TP orders, position size and leverage.
        '''
        pass

    def evaluate_price_action(self, market: Market) -> List[Todos]:
        ''' Creates commands for Trader class according results
            of strategy rules applied on price action
            Rules:
                1.) Market is always in 1 position
                2.) Position is evaluated according to last candle close and it's EMA value
        '''
        todos = []
        price_EMA_diff = self.difference_price_EMA(market)
        if market.in_position():
            market_position = market.positions[0]
            position_side = market_position.specs['side']

            if price_EMA_diff > 0:
                if position_side == 'buy':
                    print('Price closed above and doing nothing for now')
                elif self.position_is_switchable(market, price_EMA_diff):
                    todos.append(('close', market_position))
                    new_position = self.create_position(market, 'buy', price_EMA_diff)
                    todos.append(('open', new_position))
                else:
                    todos.append(('close', market_position))

            elif price_EMA_diff < 0:
                if position_side == 'sell':
                    print('Price closed below and doing nothing for now')
                elif self.position_is_closable(market, price_EMA_diff):
                    if self.position_is_switchable(market, price_EMA_diff):
                        todos.append(('close', market_position))
                        new_position = self.create_position(market, 'sell', price_EMA_diff)
                        todos.append(('open', new_position))
                    else:
                        todos.append(('close', market_position))
        else:
            new_position = None
            if self.position_is_openable(market, price_EMA_diff):
                if price_EMA_diff > 0:
                    new_position = self.create_position(market, 'buy', price_EMA_diff)
                elif price_EMA_diff < 0:
                    new_position = self.create_position(market, 'sell', price_EMA_diff)
                if new_position is not None:
                    todos.append(('open', new_position))
        return todos

    
