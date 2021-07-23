#%%
from strategy_config import EMA_INTERVAL
from pandas.core.accessor import register_dataframe_accessor
from pandas.io.formats import style
from Position import Order, Position
from Strategy import Strategy
from datetime import datetime, timedelta
from Market import Market
import pandas as pd
from FtxClient import FtxClient
from typing import Any, Dict, Optional, Tuple, List
import mplfinance as mpf

Stop_loss = Optional[Order]
Take_profit = Optional[Order]
Trade = Tuple[Order, Position]

class MainBotClass:
    messenger: FtxClient = None
    watched_markets: Dict[str, Market] = None

    def __init__(self, markets: List[str]) -> None:
        self.messenger = FtxClient()
        self.watched_markets = dict()
        for market_name in markets:
            self.add_market(market_name)
        self.strategy = Strategy(self.watched_markets)

    def add_market(self, market_name: str) -> None:
        try:
            self.messenger.get_market(market_name)
        except Exception as e:
            # Log error event (commandline print for now):
            print(e)
        else:
            # gets me last 24 hours of price action in 5M chart
            start_time = (datetime.now() - timedelta(hours=24)).timestamp()
            market_prices = \
                pd.DataFrame(self.messenger.get_historical_prices(market=market_name, 
                                                                  resolution=300, 
                                                                  start_time=start_time
                                                                  )) 
            market_prices.drop(columns=['time', 'volume'], inplace=True)
            market_position = self.get_market_position(market_name)
            self.watched_markets[market_name] = Market(market_name, market_prices, market_position)

    def get_market_position(self, market_name: str) -> Position:
        sl_order, tp_orders = self.recog_orders(market_name, self.messenger.get_conditional_orders(market_name))
        position = self.messenger.get_position(name=market_name)
        if sl_order and tp_orders and position:
            return Position(position, sl_order, tp_orders, is_triggered=True)
        elif not position:
            return None
        else:
            # log error event (print for now) and exit program
            print('Error: something is missing (SL or TP) in call get_market_position({})'.format(market_name))
            return None
            

    def recog_orders(self, market_name: str, orders: List[dict]) -> Tuple[Stop_loss, List[Take_profit]]:
        '''
        Sorts existing orders in order: Stop_loss, List[Take_profit]
        Works only for Strategy that uses 1 position (therefore many TP and exactly 1 SL order )
        '''
        if not orders:
            return None, None
        Sl_order = None
        Tp_orders = []
        for order in orders:
            if order['type'] == 'stop' or order['type'] == 'trailingStop':
                Sl_order = Order(order)
            else:
                Tp_orders.append(order)
        return Sl_order, Tp_orders

    def update_price_data(self) -> None:
        for market in self.watched_markets.values():
            start_time = (datetime.strptime(market.price_data.tail(1).iloc[0,0], 
                                           '%Y-%m-%dT%H:%M:%S+00:00'
                                           ) + timedelta(minutes=5)).timestamp()
            market.append_price_data(self.messenger.get_historical_prices(market=market.name, 
                                                                          resolution=300, 
                                                                          start_time=start_time 
                                                                          ))

    def apply_strategy(self) -> Dict[str, List[Trade]]:
        new_trades = dict()
        for market in self.watched_markets.values():
            possible_trade = self.strategy.evaluate_market(market)
            if possible_trade is not None:
                new_trades[market.name] = possible_trade
        return new_trades

    def plot_market_data(self, market: Market) -> None:
        data_to_plot = market.price_data.loc[EMA_INTERVAL - 1:].copy(deep=True)
        data_to_plot['startTime'] = \
            pd.to_datetime(data_to_plot['startTime'].apply(lambda date: datetime.strptime(date, '%Y-%m-%dT%H:%M:%S+00:00')))
        data_to_plot.set_index('startTime', inplace=True)
        ema21 = mpf.make_addplot(self.strategy.markets_EMAs[market.name]['EMA'])
        mpf.plot(data_to_plot, type='candle', style='charles', addplot=ema21) # vie tiez savevovat obrazky plotu
        
a = MainBotClass(['BTC/USD'])
arg = a.watched_markets['BTC/USD']
a.plot_market_data(arg)
print()
# %%
