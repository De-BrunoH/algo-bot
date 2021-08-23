import pandas as pd
from Position import Order, Position
from datetime import timedelta
from Market import Market
from typing import Dict, List, Optional, Tuple
from trader_config import ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE, ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN, BETWEEN_ITERATION_MINUTES, MOVING_SL_PERC, REWARD_PER_TRADE, RISK_PER_TRADE, SL_IN_TRADE_PERCENTAGE, USED_EMAS
from trader_config import Market_name, Stop_loss, Take_profit, EMA_data, Time, Todos, Trade


class multi_EMA_strategy:
    ''' 
        Base functions: (public functions used in other classes)
            - evaluate_market(...)
            - pack_data_for_plot(...)
    '''

    update_checkpoint = timedelta(minutes=BETWEEN_ITERATION_MINUTES)
    used_EMAs = USED_EMAS
    markets_EMAs: Dict[Market_name, Dict[int, pd.DataFrame]] = dict()
    market_last_check: Dict[Market_name, Dict[int, Time]] = dict()

    def __init__(self, markets: List[Market_name]) -> None:
        for market_name in markets:
            self.markets_EMAs[market_name] = dict()
            self.market_last_check[market_name] = dict()

    def evaluate_market(self, account_info: dict,
                        market: Market) -> List[Todos]:
        self._calculate_all_emas(market)
        if market.in_position():
            self._update_sl(market, market.positions[0])
        todos = self.evaluate_price_action(account_info, market)
        return todos

    def pack_data_for_plot(self, market: Market) -> Dict[int, pd.DataFrame]:
        self._calculate_all_emas(market)
        processed_plot_data = dict()
        max_ema_interval = max(self.used_EMAs)
        for interval, values in self.markets_EMAs[market.name].items():
            processed_plot_data[interval] = list(values['EMA'])[max_ema_interval - interval + 1:]
        return processed_plot_data

    def reset(self) -> None:
        for market_name in self.markets_EMAs.keys():
            self.markets_EMAs[market_name] = dict()
            self.market_last_check[market_name] = dict()

    def _calculate_all_emas(self, market: Market) -> None:
        for ema in self.used_EMAs:
            self._calculate_EMA(market, ema)

    def _update_sl(self, market: Market, position: Position) -> None:
        sl_order = position.stop_losses[0]
        new_sl = self._get_last_EMA(market, 21) * ((1 - MOVING_SL_PERC) if position.specs['side'] == 'buy' else (1 + MOVING_SL_PERC))
        sl_order.specs['trigger_price'] = max(new_sl, position.initi_sl_trigger_price) if position.specs['side'] == 'buy' else min(new_sl, position.initi_sl_trigger_price)

    def _calculate_EMA(self, market: Market, interval: int) -> None:
        max_ema_interval = max(self.used_EMAs)
        last_EMA = market.price_data['close'].loc[max_ema_interval - interval:max_ema_interval - 1].sum(axis=0) / interval \
            if interval not in self.market_last_check[market.name].keys() else self._get_last_EMA(market, interval)

        relevant_candles = market.price_data.loc[interval:] if interval not in self.market_last_check[market.name].keys() \
            else market.price_data.loc[market.price_data['time'] > self.market_last_check[market.name][interval]]

        market_EMAs = {
            'time': [],
            'EMA': []
        }

        for _, row in relevant_candles.iterrows():
            close = row['close']
            time = row['time']
            last_EMA = (2 / (interval + 1)) * close + \
                (1 - (2 / (interval + 1))) * last_EMA
            market_EMAs['time'].append(time)
            market_EMAs['EMA'].append(last_EMA)

        self.markets_EMAs[market.name][interval] = pd.DataFrame(market_EMAs)
        self.market_last_check[market.name][interval] = market_EMAs['time'][-1]

    def _get_last_EMA(self, market: Market, interval: int) -> float:
        return self.markets_EMAs[market.name][interval]['EMA'].tail(1).iloc[0]

    def _difference_price_EMA(self, market: Market, interval: int) -> float:
        return market.get_last_price_close() - self._get_last_EMA(market, interval)

    def _can_open_position(self, market: Market, price_lowEMA_diff: float,
                          price_highEMA_diff: float, side: str) -> bool:
        ''' Returns if position can be opened. (is in acceptable range)
        '''
        if (side == 'buy' and price_highEMA_diff < 0) or (
                side == 'sell' and price_highEMA_diff > 0):
            return False
        return ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN >= (
            abs(price_highEMA_diff) / market.get_last_price_close()) # zmena z ema 21 na ema 200

    def _can_close_position(self, market: Market,
                           price_lowEMA_diff: float) -> bool:
        ''' Returns if position can be closed. (is in acceptable range)
        '''
        return ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE <= (
            abs(price_lowEMA_diff) / market.get_last_price_close())

    def _asses_risk(self, account_info: dict, market: Market, sl_side: str,
                   price_lowEMA_diff: float) -> Tuple[float, Order, float]:
        ''' Calculates position sizing and SL order according to strategy risk managment.
        '''
        perc_sl_EMA = (
            1 +
            SL_IN_TRADE_PERCENTAGE) if sl_side == 'buy' else (
            1 -
            SL_IN_TRADE_PERCENTAGE)
        trigger_price = self._get_last_EMA(market, 21) * perc_sl_EMA
        if sl_side == 'sell':
            perc_sl_last_close = abs(
                perc_sl_EMA - (abs(price_lowEMA_diff) / market.get_last_price_close()) - 1)
        else:
            perc_sl_last_close = abs(
                perc_sl_EMA + (abs(price_lowEMA_diff) / market.get_last_price_close()) - 1)
        account_sizing = RISK_PER_TRADE / perc_sl_last_close
        leverage = account_sizing
        collat_size = account_sizing * account_info['collateral']
        size = collat_size / market.get_last_price_close()

        sl_specs = {
            "market": market.name,
            "side": sl_side,
            "triggerPrice": trigger_price,
            "size": size,
            "type": "stop",
            "reduceOnly": True
        }

        return size, Order('conditional', sl_specs), leverage

    def _asses_reward(self, market: Market, tp_side: str,
                     size: float) -> Take_profit:
        ''' Calculates take profit order according to rules.
        '''
        trigger_price = market.get_last_price_close() * (1 - REWARD_PER_TRADE if tp_side ==
                                                         'buy' else 1 + REWARD_PER_TRADE)
        tp_specs = {
            "market": market.name,
            "side": tp_side,
            "triggerPrice": trigger_price,
            "size": size,
            "type": "takeProfit",
            "reduceOnly": True,
            "retryUntilFilled": True
        }
        return Order('conditional', tp_specs)

    def _create_trade(self, account_info: dict, market: Market,
                     side: str, price_lowEMA_diff: float) -> Trade:
        ''' Creates new position on market side according to rules.
            Sets SL and TP orders, position size and leverage.
        '''
        size, sl_order, leverage = self._asses_risk(
            account_info, market, 'buy' if side == 'sell' else 'sell', price_lowEMA_diff)
        order_specs = {
            'market': market.name,
            'side': side,
            'price': None,
            'size': size,
            'type': 'market',
            'reduceOnly': False,
            'ioc': False,
            'postOnly': False,
            'clientId': None
        }
        position_order = Order('normal', order_specs)
        position = Position(None, leverage, [sl_order], [self._asses_reward(
            market, 'buy' if side == 'sell' else 'sell', size)], is_triggered=False)
        return (position_order, position)

    def _create_close_order(self, position: Position) -> Order:
        side = 'buy' if position.specs['side'] == 'sell' else 'sell'
        close_order = {
            "market": position.specs['future'],
            "side": side,
            "price": None,
            "type": "market",
            "size": position.specs['size'],
            "reduceOnly": True,
            "ioc": False,
            "postOnly": False,
            "clientId": None
        }
        return Order('normal', close_order)

    def _update_position(self, account_info: dict, position: Position, market: Market,
                        price_lowEMA_diff: float, price_highEMA_diff: float, evaluated_side: str) -> List[Todos]:
        ''' Checks if price can be closed or even more switched in oposite direction.
            Returns list of todos for trader that will handle what needs to be done.
        '''
        todos = []
        if position.specs['side'] == evaluated_side:
            needed_word = 'above' if evaluated_side == 'buy' else 'below'
            print(f'Price closed {needed_word} EMA and doing nothing for now')
        elif not self._can_close_position(market, price_lowEMA_diff):
            needed_words = 'above EMA on sell' if evaluated_side == 'buy' else 'below EMA on buy'
            print(
                f'Price closed {needed_words} side of the trade but is in acceptable range')
        else:
            todos.append(
                ('close', (self._create_close_order(position), position)))
            if self._can_open_position(
                    market, price_lowEMA_diff, price_highEMA_diff, evaluated_side):
                todos.append(
                    ('open',
                     self._create_trade(
                         account_info,
                         market,
                         evaluated_side,
                         price_lowEMA_diff)))
        return todos

    def evaluate_price_action(self, account_info: dict,
                              market: Market) -> List[Todos]:
        ''' Creates commands for Trader class according results
            of strategy rules applied on price action
            Rules:
                1.) Market is always in 1 position
                2.) Position is evaluated according to last candle close and it's EMA value
        '''
        todos = []
        price_lowEMA_diff = self._difference_price_EMA(market, min(self.used_EMAs))
        price_highEMA_diff = self._difference_price_EMA(market, max(self.used_EMAs))
        if market.in_position():
            market_position = market.positions[0]
            if price_lowEMA_diff > 0:
                todos = self._update_position(
                    account_info,
                    market_position,
                    market,
                    price_lowEMA_diff,
                    price_highEMA_diff,
                    'buy')
            elif price_lowEMA_diff < 0:
                todos = self._update_position(
                    account_info,
                    market_position,
                    market,
                    price_lowEMA_diff,
                    price_highEMA_diff,
                    'sell')
        else:
            new_position = None
            if price_lowEMA_diff > 0 and self._can_open_position(
                    market, price_lowEMA_diff, price_highEMA_diff, 'buy'):
                new_position = self._create_trade(
                    account_info, market, 'buy', price_lowEMA_diff)
            elif price_lowEMA_diff < 0 and self._can_open_position(market, price_lowEMA_diff, price_highEMA_diff, 'sell'):
                new_position = self._create_trade(
                    account_info, market, 'sell', price_lowEMA_diff)
            if new_position is not None:
                todos.append(('open', new_position))
        return todos
