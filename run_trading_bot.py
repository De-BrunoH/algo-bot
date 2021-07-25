from EMA_strategy import EMA_strategy
from Ftx_client import Ftx_client
from Trader import Trader
from trader_config import INIT_MARKETS

# API used:
BROKER_API = Ftx_client()

# Strategy:
STRATEGY = EMA_strategy(INIT_MARKETS)


def run_trading_bot() -> None:
    # intialization
    trader = Trader(INIT_MARKETS, BROKER_API, STRATEGY)

    while True:
        trader.engage_routine()
        # sleep(STRATEGY_PAUSE)


def test_trader() -> None:
    trader = Trader(INIT_MARKETS, BROKER_API, STRATEGY)
    print(trader.watched_markets)
    print(trader.watched_markets['BTC-PERP'].price_data)

def test_api_client() -> None:
    a = Ftx_client()
    b = a.get_position('BTC-PERP')
    c = a.get_fills_market('BTC-PERP')
    print(b)
    print(c)
        
test_trader()
#test_api_client()
        