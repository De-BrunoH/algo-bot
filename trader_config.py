from typing import Dict, List, Tuple, Optional
from Position import Position, Order

Market_name = str
Stop_loss = Optional[Order]
Take_profit = Optional[Order]
Leverage = float
Trade = Tuple[Order, Position, Leverage]
Time = float
EMA_value = float
EMA_data = Tuple[Time, EMA_value]
Command = List[str]
Todos = List[Tuple[Command, Position]]

# Trader config:
INIT_MARKETS = [
    'BTC-PERP'
]

# Offline trader config:
ACCOUNT_BALANCE = 1000

# Offline trader config:
TEST_INIT_MARKETS = [
    ('ETH-PERP', '2020-01-01T00:00:00+00:00')
]

# Statistics:
LOSS_STREAK_RANGE = 3
WIN_STREAK_RANGE = 1

# Logger
REAL_TIME_LOG_FILE = 'real_time_trader.log'
TEST_LOG_FILE = 'test_run.log'

# Strategy:
# big profit longterm nastavenia
MAX_LEVERAGE = 4
LOOP_PAUSE = 300
USED_EMAS = [
    21,
    55
]
# ak sa podari prerabanie do class mozes zmazat
MAX_EMA_INTERVAL = 55
EMA_INTERVAL = 21
START_PRICE_RANGE_1H = 3
# =============================================
START_PRICE_DATA_RANGE = max(USED_EMAS)
BETWEEN_ITERATION_MINUTES = 180
PRICE_RANGE_5M = 4
CANDLESTICK_RESOLUTION = 3600

RISK_PER_TRADE = 0.01
REWARD_PER_TRADE = 0.1
MOVING_SL_PERC = 0.005
SL_IN_TRADE_PERCENTAGE = 0.001
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE = 0.015
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN = 0.02

'''
MAX_LEVERAGE = 4
LOOP_PAUSE = 300
MAX_EMA_INTERVAL = 200
BETWEEN_ITERATION_MINUTES = 15
PRICE_RANGE_5M = 4
CANDLESTICK_RESOLUTION = 300
# ===================================
# 1400 end balance multiEMA_startegy | market: ('BTC-PERP', '2021-07-15T00:00:00+00:00')
# neprepisuj len zakomentuj ked tak nech na to nezabudneme

RISK_PER_TRADE = 0.01
REWARD_PER_TRADE = 0.3
SL_IN_TRADE_PERCENTAGE = 0.001
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE = 0.01
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN = 0.03

# ===================================
'''