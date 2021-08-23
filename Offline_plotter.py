


from datetime import datetime
import pandas as pd
import mplfinance as mpf
from Market import Market
from Statistics import Statistics
from Ftx_client import Ftx_client
from multi_EMA_strategy import multi_EMA_strategy
from trader_config import CANDLESTICK_RESOLUTION, Market_name


class Offline_plotter:
    ''' 
        Base functions: (public functions used in other classes)
            - plot_strategy_on_market(...)
    '''

    strategy: multi_EMA_strategy = None
    price_data: list = None

    def __init__(self,strategy: multi_EMA_strategy, price_data: list) -> None:
        if isinstance(strategy, multi_EMA_strategy):
            self.strategy = strategy
            self.price_data = price_data
        else:
            raise Exception('Error: Invalid parameters passed to Offline_plotter.')

    def plot_strategy_on_market(self, market_name: Market_name,
                                strategy_data: list, statistics_data: list) -> None:
        market = Market(
            market_name,
            positions=[],
            price_data=pd.DataFrame(self.price_data))
        self._plot_market_data(market, strategy_data, statistics_data)

    def _plot_market_data(self, market: Market, strategy_data: dict, statistics_data: dict) -> None:
        data_to_plot = market.price_data.loc[max(self.strategy.used_EMAs):len(market.price_data) - 2].copy(deep=True)
        data_to_plot['startTime'] = \
            pd.to_datetime(
            data_to_plot['startTime'].apply(
                lambda date: datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S+00:00')))
        data_to_plot.set_index('startTime', inplace=True)

        df_stats = pd.DataFrame(statistics_data)
        df_buys = df_stats['buys']
        df_sells = df_stats['sells']
        df_d_sells = df_stats['double_sells']
        df_d_buys = df_stats['double_buys']
        df_account_balances = df_stats['balances']
        plot_addons = [
            mpf.make_addplot(pd.DataFrame(strategy_data)),
            mpf.make_addplot(df_buys, **{'scatter': True, 'marker': '^', 'markersize': 75, 'color': '#00ff00'}),
            mpf.make_addplot(df_d_buys, **{'scatter': True, 'marker': '^', 'markersize': 75, 'color': '#00ff00'}),
            mpf.make_addplot(df_sells, **{'scatter': True, 'marker': 'v', 'markersize': 75, 'color': '#ff0000'}),
            mpf.make_addplot(df_d_sells, **{'scatter': True, 'marker': 'v', 'markersize': 75, 'color': '#ff0000'}),
            mpf.make_addplot(df_account_balances, **{'color': 'w', 'panel': 1})
        ]
        mpf.plot(data_to_plot, type='candle', style='mike', addplot=plot_addons)