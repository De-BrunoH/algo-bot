from trader_config import Trade
from typing import List, Set, Tuple
from Position import Position
import pandas as pd


class Market:
    def __init__(self, name: str, positions: List[Position],
                 price_data: pd.DataFrame = pd.DataFrame()) -> None:
        self.name = name
        self.positions: List[Position] = positions
        self.waiting_trades: List[Trade] = []
        self.price_data = price_data

    def __repr__(self) -> str:
        return f'Market: {self.name}'

    def in_position(self) -> bool:
        return len(self.positions) != 0

    def add_position(self, new_position: Position) -> None:
        self.positions.append(new_position)

    def remove_position(self, position: Position) -> None:
        self.positions.remove(position)

    def add_waiting_trade(self, trade: Trade) -> None:
        self.waiting_trades.append(trade)

    def load_price_data(self, price_data: pd.DataFrame) -> None:
        self.price_data = price_data

    def get_last_price_close(self) -> float:
        return self.price_data['close'].tail(1).iloc[0]

    def get_last_price_high(self) -> float:
        return self.price_data['high'].tail(1).iloc[0]

    def get_last_price_low(self) -> float:
        return self.price_data['low'].tail(1).iloc[0]

    def get_last_price_time(self) -> float:
        return self.price_data.tail(1).iloc[0, 1]

    def get_last_price_time_string(self) -> str:
        return self.price_data['startTime'].tail(1).iloc[0]
