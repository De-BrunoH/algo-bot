from typing import Dict, List, Tuple, Optional
from Position import Position, Order

Market_name = str
Stop_loss = Optional[Order]
Take_profit = Optional[Order]
Trade = Tuple[Order, Position]
Time = float
EMA_value = float
EMA_data = Tuple[Time, EMA_value]
Command = List[str]
Todos = List[Tuple[Command, Position]]

# Trader config:
INIT_MARKETS = [
    'BTC-PERP',
    'ETH/USD'
]

# API used:
#BROKER_API = Ftx_client()

# Strategy:
#STRATEGY = EMA_strategy(INIT_MARKETS)

EMA_INTERVAL = 21
START_PRICE_RANGE_1H = 24
PRICE_RANGE_5M = 4
CANDLESTICK_RESOLUTION = 300
