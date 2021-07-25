from typing import Tuple
from numpy import positive
from pandas._libs.tslibs.timestamps import Timestamp
from Position import Order, Position
from EMA_strategy import EMA_strategy
from trader_config import CANDLESTICK_RESOLUTION, START_PRICE_RANGE_1H, Trade
from trader_config import Market_name, List,Dict
from Ftx_client import Ftx_client
from datetime import timedelta, datetime
import pandas as pd
from Market import Market

class Trader:
    messenger: Ftx_client = None
    strategy: EMA_strategy = None
    watched_markets: Dict[str, Market] = dict()


    def __init__(self, markets_to_watch: List[Market_name], api_client: Ftx_client, strategy: EMA_strategy) -> None:
        self.messenger = api_client
        self.strategy = strategy
        for market_name in markets_to_watch:
            self._add_market(market_name)

    def engage_routine(self) -> None:
        for market in self.watched_markets.values():
            self.update_price_data(market)
            self.apply_strategy(market)
            self.update_positions(market)

    def _get_market_data(self, market_name) -> Market:
        ''' Gets market data in right format '''
        start_time = (datetime.now() - timedelta(hours=START_PRICE_RANGE_1H)).timestamp()
        market_prices = \
            pd.DataFrame(self.messenger.get_historical_prices(market=market_name, 
                                                                resolution=CANDLESTICK_RESOLUTION, 
                                                                start_time=start_time
                                                                )[:-1])
        market_position = self._get_market_position(market_name)
        return Market(market_name, market_position, market_prices)

    def _get_market_position(self, market_name: str) -> Position:
        sl_order, tp_orders = self.strategy.recog_orders(self.messenger.get_conditional_orders(market_name))
        position = self.messenger.get_position(market=market_name)
        if sl_order and tp_orders and position:
            return Position(position, sl_order, tp_orders, is_triggered=True)
        elif not position:
            return None
        else:
            # log error event (print for now) and exit program
            print(f'Error: something is missing (SL or TP) in call get_market_position({market_name})')
            return None    

    def _add_market(self, market_name: str) -> None:
        try:
            self.messenger.get_market(market_name)
        except Exception as e:
            # Log error event (commandline print for now):
            print(f'Error: {e}')
        else:
            self.watched_markets[market_name] = self._get_market_data(market_name)
            # treba checknut skuskou ze ako vyzera nulova pozicia
            if not self.watched_markets[market_name].positions:
                self.messenger.cancel_orders(market_name)

    def apply_strategy(self, market: Market) -> None:
        possible_trade = self.strategy.evaluate_market(market)
        if possible_trade is not None:
            market.add_waiting_position(possible_trade)

    def update_positions(self, market: Market) -> None:
        start_time = (datetime.now() - timedelta(minutes=10)).timestamp() # last check should be given plus 1 more minutes
        new_waiting_trades = []
        for waiting_trade in market.waiting_trades:
            position_triggered = self.messenger.get_fills_market(market, start_time, order_id=waiting_trade[0]['orderId'])
            if position_triggered:
                new_position = waiting_trade[1]
                new_position.update_specs(self.messenger.get_position_by_specs(position_triggered['price']))
                self._place_orders(new_position.stop_losses + new_position.take_profits)
                new_position.triggered_successfully()
                market.add_position(new_position)
            else:
                new_waiting_trades.append(waiting_trade)
        market.replace_waiting_trades(new_waiting_trades)


    def _palce_orders(self, orders: List[Order]) -> List[dict]:
        placed_orders = []
        for order in orders:
            if order.type == 'conditional':
                placed_orders.append(self.messenger.place_conditional_order(
                    market=order.specs['market'],
                    side=order.specs['side'],
                    trigger_price=order.specs['triggerPrice'],
                    trail_value=order.specs['trailValue'],
                    size=order.specs['size'],
                    reduce_only=order.specs['reduceOnly'],
                    type=order.specs['type'],
                    cancel=order.specs['cancelLimitOnTrigger'],
                    limit_price=order.specs['orderPrice']
                ))
            elif order.type == 'normal':
                placed_orders.append(self.messenger.place_order(
                    market=order.specs['market'],
                    side=order.specs['side'],
                    price=order.specs['price'],
                    size=order.specs['size'],
                    type=order.specs['limit'],
                    reduce_only=order.specs['reduceOnly'],
                    ioc=order.specs['ioc'],
                    post_only=order.specs['postOnly'],
                    client_id=order.specs['clientId']
                ))
        return placed_orders

    def update_price_data(self, market: Market) -> None:
        #start_time = (datetime.strptime(market.price_data.tail(1).iloc[0,0], 
        #                                '%Y-%m-%dT%H:%M:%S+00:00'
        #                                ) + self.strategy.update_checkpoint).timestamp()
        # mozno bude fungovat aj takto 
        start_time = market.price_data.tail(1).iloc[0,1] + self.strategy.update_checkpoint.timestamp()
        market.load_price_data(pd.DataFrame(self.messenger.get_historical_prices(market=market.name, 
                                                                                 resolution=CANDLESTICK_RESOLUTION, 
                                                                                 start_time=start_time 
                                                                                 )[:-1]))
