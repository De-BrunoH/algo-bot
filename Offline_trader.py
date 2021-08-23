from Offline_plotter import Offline_plotter
from Statistics import Statistics
import matplotlib.pyplot as plt
import logging
import pandas as pd
from Position import Order, Position
from Ftx_client import Ftx_client
from typing import Any, List, Optional, Tuple
from multi_EMA_strategy import multi_EMA_strategy
from datetime import datetime
from Market import Market
from trader_config import CANDLESTICK_RESOLUTION, LOSS_STREAK_RANGE, MAX_EMA_INTERVAL, Market_name, START_PRICE_DATA_RANGE, Todos, WIN_STREAK_RANGE
from Position import Position
import mplfinance as mpf

class Offline_trader:
    ''' Base functions: 
            - run_strategy_offline(...)
    '''
    api: Ftx_client = None
    strategy: multi_EMA_strategy = None
    statistics: Statistics = None
    plotter: Offline_plotter = None
    account: dict = None
    tested_markets = None


    def __init__(self, tested_markets: List[Tuple[str, str]], api: Ftx_client, 
                 strategy: multi_EMA_strategy) -> None:
        if isinstance(api, Ftx_client) and isinstance(strategy, multi_EMA_strategy):
            self.api = api
            self.strategy = strategy
            self.statistics = Statistics()
            self.account = self.api.get_account_info()
            self.tested_markets = tested_markets
        else:
            raise Exception('Error: Invalid parameters passed to Offline_plotter.')

    def run_strategy_offline(self, starting_balance: float) -> None:
        logging.info(f'Offline strategy test started.')
        for market_name, start_time in self.tested_markets:
            self._set_account_balance(starting_balance)
            logging.info(f'Starting iteration for market [{market_name}].')

            price_data = self.api.get_all_historical_prices(
                market_name, resolution=CANDLESTICK_RESOLUTION, start_time=start_time)
            self.plotter = Offline_plotter(self.strategy, price_data)
            logging.info(f'Obtained price data since {start_time}.')

            start = 0
            end = START_PRICE_DATA_RANGE + 1
            market = Market(market_name, positions=[],
                            price_data=pd.DataFrame(price_data[start:end]))

            logging.info('Starting to process price data.')
            while end < len(price_data):
                self._check_conditional_closes(market)
                todos = self.strategy.evaluate_market(self.account, market)
                self._process_todos(market, todos)
                self.statistics.update_stats('account_balance', self.account['collateral'])
                start = end
                end = end + 1
                market.price_data = pd.DataFrame(price_data[start:end])

            logging.info('End of price data processing.')
            logging.info(f'End of iteration for market [{market_name}].')
            logging.info('Processing statistics data.')
            logging.info(self.statistics.analyze_trades(self.account['collateral']))
            market.load_price_data(pd.DataFrame(price_data))
            self.strategy.reset()
            strategy_data = self.strategy.pack_data_for_plot(market)
            statistics_data = self.statistics.pack_data_for_plot(market, self.strategy)
            self.plotter.plot_strategy_on_market(market.name, strategy_data, statistics_data)
            logging.info('Ploted chart and positions and account progress.')
        logging.info('End of strategy test.')
        # for plot to stay opened
        plt.show()

    def _set_account_balance(self, starting_balance: float) -> None:
        self.account['collateral'] = starting_balance
        self.account['freeCollateral'] = starting_balance
        
    def _check_conditional_closes(self, market: Market) -> None:
        ''' Checks if any SL or Tp got hit and
            processes that position accordingly.
        '''
        for position in market.positions:
            for sl in position.stop_losses:
                if self._order_hit(market, sl):
                    self._close_position(market, sl, position, 'sl')
                    return None
            for tp in position.take_profits:
                if self._order_hit(market, tp):
                    self._close_position(market, tp, position, 'tp')
                    return None

    def _order_hit(self, market: Market, order: Order) -> bool:
        return market.get_last_price_low(
            ) <= order.specs['triggerPrice'] <= market.get_last_price_high()

    def _calculate_percentage_trade_result(
            self, close_price: float, position: Position) -> float:
        trade_percentage_collateral_result = position.specs['entryPrice'] / close_price
        return (1 - trade_percentage_collateral_result) if position.specs['side'] == 'buy' else (
            trade_percentage_collateral_result - 1)


    def _process_todos(
            self, market: Market, todos: List[Tuple[str, Any]]) -> None:
        for command, cargo in todos:
            if command == 'open':
                open_order, position = cargo
                self._open_position(market, open_order, position)
            elif command == 'close':
                close_order, position = cargo
                self._close_position(market, close_order, position)
 
    def _open_position(self, market: Market, order: Order, position: Position) -> None:
        if order.specs['type'] == 'market':
            entry_price = market.get_last_price_close()
            cost = order.specs['size'] * entry_price
            position.update_specs({
                "cost": cost,
                "entryPrice": entry_price,
                "estimatedLiquidationPrice": None,
                "future": market.name,
                "initialMarginRequirement": 0.1,
                "longOrderSize": None,
                "maintenanceMarginRequirement": 0.03,
                "netSize": (- order.specs['size']) if order.specs['side'] == 'sell' else order.specs['size'],
                "openSize": None,
                "realizedPnl": 0,
                "shortOrderSize": None,
                "side": order.specs['side'],
                "size": order.specs['size'],
                "unrealizedPnl": 0,
                "collateralUsed": cost
            })
            market.add_position(position)
            position.set_open_time(market.get_last_price_time_string())
            self._deduce_fee(transaction_cost=cost, fee_type='takerFee')

            self._print_log(
                'opened',
                market.get_last_price_time_string(),
                position
            )

        else:
            # tuto vetvu treba este domysliet nieco na styl ze to pacnes
            # do waiting trades a a dalsiu iteraciu skontrolujes ci hittlo
            entry_price = order.specs['price']
            # ==================================

    def _deduce_fee(self, fee_type: str, transaction_cost: float) -> None:
        ''' fee_type should 'takerFee' or 'makerFee'
        '''
        fee_cost = abs(self.account[fee_type] * transaction_cost)
        self.account['freeCollateral'] -= fee_cost
        self.account['collateral'] -= fee_cost


    def _check_waiting_trades(market: Market) -> None:
        ''' Checks if any of waiting trades got triggered.
        '''
        # not needed for this strategy
        pass

    def _print_log(self, action: str, candle_time: str, position: Position,
                result: float = None, balance: float = None, terminatoin_reason: str = None):
        """ msg
        """

        msg = f"time: {candle_time} | Position {action}: {position}"

        if action == 'closed' or action == 'forcibly closed':
            msg += f"| raw_result: {result}% | account_result = {result * position.leverage} | balance: {balance}"

        elif action == 'update':
            msg += f"| raw_result: {result}% | account_result = {result * position.leverage} | balance: {balance} | Termination reason: {terminatoin_reason}"

        logging.info(msg)

    def _close_position(self, market: Market, order: Order, position: Position, 
                        trigger_type: str = None) -> None:
        order_price = order.specs['triggerPrice'] \
                        if order.type == 'conditional' else (market.get_last_price_close() \
                            if order.specs['type'] == 'market' else order.specs['price'])
        perc_result = self._calculate_percentage_trade_result(
            order_price, position)
        trade_raw_collateral_result = position.specs['collateralUsed'] * perc_result
        self.account['collateral'] += trade_raw_collateral_result
        self.account['freeCollateral'] += trade_raw_collateral_result
        self._deduce_fee(transaction_cost=position.specs['cost'], fee_type='takerFee')
        position.set_close_time(market.get_last_price_time_string())
        close_reason = 'rules' if order.type == 'normal' else trigger_type + '_hit'

        self._print_log(
            'closed' if trigger_type is None else 'forcibly closed',
            market.get_last_price_time_string(),
            position,
            round(perc_result * 100, 2),
            self.account['collateral'],
            close_reason
        )

        market.remove_position(position)
        self.statistics.update_stats('trades', {
            'open_time': position.open_time,
            'close_time': position.close_time,
            'side': position.specs['side'],
            'result': perc_result,
            'close_reasoning': close_reason,
            'entry_price': position.specs['entryPrice'],
            'close_price': order_price
        })
