from trader_config import ACCOUNT_BALANCE
from Offline_trader import Offline_trader
from multi_EMA_strategy import multi_EMA_strategy
from Ftx_client import Ftx_client
from Trader import Trader
from Offline_trader import Offline_trader
from trader_config import INIT_MARKETS, LOOP_PAUSE, REAL_TIME_LOG_FILE, TEST_INIT_MARKETS, TEST_LOG_FILE
import logging
from time import sleep

# API used:
BROKER_API = Ftx_client()

# Strategy:
#STRATEGY = multi_EMA_strategy(INIT_MARKETS)
# Strategy test
STRATEGY_TEST = multi_EMA_strategy([market[0] for market in TEST_INIT_MARKETS])

def run_trading_bot(api: Ftx_client, strategy: multi_EMA_strategy) -> None:
    logging.basicConfig(
        filename=REAL_TIME_LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s')
    logging.info('Beggining initialization of Trader class.')
    trader = Trader(INIT_MARKETS, api, strategy)
    logging.info('Ending Initialization.')
    logging.info('Begging main loop of Trader.')
    while True:
        if not trader.engage_routine():
            break
        sleep(LOOP_PAUSE)
    logging.info('Ending main loop of Trader.')
    logging.info('Shutting down Trader.')


def run_offline_trading_bot(api: Ftx_client, strategy: multi_EMA_strategy) -> None:
    logging.basicConfig(
        filename=TEST_LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s'
    )
    logging.info('Beggining initialization of Trader class.')
    fake_trader = Offline_trader(TEST_INIT_MARKETS, api, strategy)
    logging.info('Ending Initialization.')
    logging.info('Begging main loop of Offline trader.')
    fake_trader.run_strategy_offline(ACCOUNT_BALANCE)
    logging.info('Ending main loop of Offline trader.')
    logging.info('Shutting down Offline trader.')


if __name__ == '__main__':
    #run_trading_bot(BROKER_API, STRATEGY)
    run_offline_trading_bot(BROKER_API, STRATEGY_TEST)