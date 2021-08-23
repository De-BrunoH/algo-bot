from os import close
from typing import List


class Order:

    def __init__(self, type: str, api_order: dict) -> None:
        ''' type: 'normal' or 'conditional'
        '''
        self.type = type
        self.specs = api_order

    def __str__(self) -> str:
        typos = self.specs['type']
        market = self.specs['market']
        if self.type == 'normal':
            price = self.specs['price']
            return f'[price: {price}]'
        else:
            trig_price = self.specs['triggerPrice']
            order_price = None  # self.specs['orderPrice']
            return f'[trigger price: {trig_price}]'

    def __repr__(self) -> str:
        return self.__str__()


class Position:
    def __init__(self, api_position: dict, leverage: float, stop_losses: List[Order],
                 take_profits: List[Order], is_triggered: bool, open_time: str = None, close_time: str = None) -> None:
        self.is_triggered = is_triggered
        self.leverage = leverage
        self.stop_losses = stop_losses
        # strategy dependant atribute
        self.initi_sl_trigger_price = stop_losses[0].specs['triggerPrice']
        # ===========================
        self.take_profits = take_profits
        self.specs = api_position
        self.open_time = open_time
        self.close_time = close_time

    def __str__(self) -> str:
        market = self.specs['future']
        side = self.specs['side']
        size = self.specs['size']
        entry_price = self.specs['entryPrice']
        return f'[market: {market}, side: {side}, size: {size}, leverage: {self.leverage}, ' + \
               f'entry: {entry_price}, SL: {self.stop_losses}, TP: {self.take_profits}]'

    def __repr__(self) -> str:
        return self.__str__()

    def update_specs(self, new_position_specs: dict) -> None:
        self.specs = new_position_specs

    def triggered_successfully(self) -> None:
        self.is_triggered = True

    def set_open_time(self, time: str) -> None:
        if self.open_time is not None:
            raise Exception('Error: Open_time already set.')
        self.open_time = time

    def set_close_time(self, time: str) -> None:
        if self.close_time is not None:
            raise Exception('Error: Close_time already set.')
        self.close_time = time
