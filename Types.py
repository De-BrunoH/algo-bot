from typing import Dict, Tuple

# Candlestick representation
High = float
Low = float
Open = float
Close = float
Volume = float
Time = str

Candlestick = Dict[Open, Close, High, Low, Volume, Time]