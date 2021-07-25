from trader_config import Trade
from typing import List, Set
from Position import Position
import pandas as pd

class Market:
    def __init__(self, name: str, positions: List[Position], price_data: pd.DataFrame = pd.DataFrame()) -> None:
        self.name = name
        self.positions: List[Position] = positions
        self.waiting_trades: List[Trade] = []
        self.price_data = price_data

    def __repr__(self) -> str:
        return f'Market: {self.name}'
    
    def is_in_position(self) -> bool:
        return len(self.positions) == 0

    def add_position(self, new_position: Position) -> None:
        self.positions.append(new_position)
    
    def load_price_data(self, price_data: pd.DataFrame) -> None:
        self.price_data = price_data
