from datetime import datetime
from time import strptime
from multi_EMA_strategy import multi_EMA_strategy
from trader_config import CANDLESTICK_RESOLUTION, LOSS_STREAK_RANGE, WIN_STREAK_RANGE, ACCOUNT_BALANCE
from Market import Market
from typing import Any, Dict, Tuple


class Statistics:

    stats: Dict[str, Any] = None

    def __init__(self) -> None:
        self.stats = dict()

    def pack_data_for_plot(self, market: Market, strategy: multi_EMA_strategy) -> dict:
        actions = {
            'buys': [],
            'sells': [],
            'double_sells': [],
            'double_buys': [],
            'balances': self.stats['account_balance']
        }
        self._add_nones(actions, 2)
        last_trade_end = datetime.strptime(
            market.price_data['startTime'].iloc[max(strategy.used_EMAs)], 
            '%Y-%m-%dT%H:%M:%S+00:00'
        )
        for trade in self.stats['trades']:
            trade_open = datetime.strptime(
                    trade['open_time'], '%Y-%m-%dT%H:%M:%S+00:00')
            trade_close = datetime.strptime(
                    trade['close_time'], '%Y-%m-%dT%H:%M:%S+00:00')
            pretrade_candles = int((trade_open - last_trade_end).total_seconds() // CANDLESTICK_RESOLUTION)
            self._add_nones(actions, pretrade_candles)
            intratrade_candles = int((trade_close - trade_open).total_seconds() // CANDLESTICK_RESOLUTION)
            if pretrade_candles == 0:
                if trade['side'] == 'sell':
                    self._process_double_sell(actions, trade, intratrade_candles)
                else:
                    self._process_double_buy(actions, trade, intratrade_candles)
            else:
                if trade['side'] == 'sell':
                    self._process_sell(actions, trade, intratrade_candles)
                else:
                    self._process_buy(actions, trade, intratrade_candles)
            last_trade_end = trade_close
        last_candles = int((
            datetime.strptime(market.price_data['startTime'].tail(1).iloc[0], '%Y-%m-%dT%H:%M:%S+00:00') - \
                 last_trade_end).total_seconds() // CANDLESTICK_RESOLUTION)
        self._add_nones(actions, last_candles) #+ 1)
        return actions

    def _process_sell(self, actions: dict, trade: dict, intratrade_candles: int) -> None:
        actions['sells'].append(trade['entry_price'])
        actions['buys'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)
        self._add_nones(actions, intratrade_candles)
        actions['buys'].append(trade['close_price'])
        actions['sells'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)

    def _process_buy(self, actions: dict, trade: dict, intratrade_candles: int) -> None:
        actions['buys'].append(trade['entry_price'])
        actions['sells'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)
        self._add_nones(actions, intratrade_candles)
        actions['sells'].append(trade['close_price'])
        actions['buys'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)

    def _process_double_sell(self, actions: dict, trade: dict, intratrade_candles: int) -> None:
        if actions['double_sells']:
            actions['double_sells'].pop()
        else:
            actions['double_buys'].append(None)
            actions['buys'].append(None)
            actions['sells'].append(None)
        actions['double_sells'].append(trade['entry_price'])  
        self._add_nones(actions, intratrade_candles)
        actions['buys'].append(trade['close_price'])
        actions['sells'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)

    def _process_double_buy(self, actions: dict, trade: dict, intratrade_candles: int) -> None:
        if actions['double_buys']:
            actions['double_buys'].pop()
        else:
            actions['double_sells'].append(None)
            actions['buys'].append(None)
            actions['sells'].append(None)
        actions['double_buys'].append(trade['entry_price'])
        self._add_nones(actions, intratrade_candles)
        actions['sells'].append(trade['close_price'])
        actions['buys'].append(None)
        actions['double_sells'].append(None)
        actions['double_buys'].append(None)

    def _add_nones(self, actions: dict, count: int) -> None:
        for _ in range(count - 1):
            actions['buys'].append(None)
            actions['sells'].append(None)
            actions['double_sells'].append(None)
            actions['double_buys'].append(None)
            
    def update_stats(self, stat: str, value: Any) -> None:
        if stat not in self.stats.keys():
            self.stats[stat] = []
        self.stats[stat].append(value)

    def analyze_trades(self, end_balance) -> str:
        trades = self.stats['trades']
        start_time = trades[0]['open_time'] if trades else None
        end_time = trades[-1]['close_time'] if trades else None

        losing_slhit_trades = [
            trade for trade in trades if trade['close_reasoning'] == 'sl_hit' and trade['result'] < 0]
        losing_other_trades = [
            trade for trade in trades if trade['close_reasoning'] == 'close' and trade['result'] < 0]
        losing_trades_results = list(
            map(lambda x: x['result'], losing_slhit_trades + losing_other_trades))
        biggest_loss = min(losing_trades_results if losing_trades_results else [0]) * 100 
        smallest_loss = max(losing_trades_results if losing_trades_results else [0]) * 100

        profit_tphit_trades = [
            trade for trade in trades if trade['close_reasoning'] == 'tp_hit']
        profit_other_trades = [
            trade for trade in trades if (trade['close_reasoning'] == 'close' or trade['close_reasoning'] == 'sl_hit') \
                and trade['result'] >= 0]
        profit_trades_results = list(
            map(lambda x: x['result'], profit_tphit_trades + profit_other_trades))
        biggest_win = max(profit_trades_results if profit_trades_results else [0]) * 100
        smallest_win = min(profit_trades_results if profit_trades_results else [0]) * 100

        loss_streaks = []
        win_streaks = []
        current_loss_streak = []
        current_win_streak = []
        for trade in trades:
            if current_loss_streak and trade['result'] >= 0:
                loss_streaks.append(current_loss_streak)
                current_loss_streak = []
            elif current_win_streak and trade['result'] < 0:
                win_streaks.append(current_win_streak)
                current_win_streak = []
            if trade['result'] < 0:
                current_loss_streak.append(trade)
            elif trade['result'] >= 0:
                current_win_streak.append(trade)
        if current_loss_streak:
            loss_streaks.append(current_loss_streak)
        if current_win_streak:
            win_streaks.append(current_win_streak)

        loss_streaks = list(map(lambda x: (len(x), x[0]['open_time'], x[-1]['close_time']), [
                            streak for streak in loss_streaks if len(streak) > LOSS_STREAK_RANGE]))
        win_streaks = list(map(lambda x: (len(x), x[0]['open_time'], x[-1]['close_time']),
                            [streak for streak in win_streaks if len(streak) > WIN_STREAK_RANGE]))
        analysis_result = \
            ('\n' + '=' * 40 + '\n') + \
            'ANALYSIS RESULT:\n' + \
            ('-' * 40 + '\n') + \
            f'Time range: {start_time} - {end_time}\n' + \
            f'Trade count        = {len(trades)}\n' + \
            f'\nLosing trades      = {len(losing_slhit_trades) + len(losing_other_trades)}\n' + \
            f'\tSL hit         = {len(losing_slhit_trades)}\n' + \
            f'\tOther reason   = {len(losing_other_trades)}\n' + \
            f'\tSmallest loss  = {round(smallest_loss, 3)}%\n' + \
            f'\tBiggest loss   = {round(biggest_loss, 3)}%\n' + \
            f'\tStreaks over {LOSS_STREAK_RANGE}:\n' + \
            f'\t\tCount         = {len(loss_streaks)}\n' + \
            f'\t\t[Len | Time]  = {loss_streaks}\n' + \
            f'\nProfitable trades  = {len(profit_tphit_trades) + len(profit_other_trades)}\n' + \
            f'\tTP hit         = {len(profit_tphit_trades)}\n' + \
            f'\tOther reason   = {len(profit_other_trades)}\n' + \
            f'\tSmallest win   = {round(smallest_win, 3)}%\n' + \
            f'\tBiggest win    = {round(biggest_win,3)}%\n' + \
            f'\tStreaks over {WIN_STREAK_RANGE}:\n' + \
            f'\t\tCount         = {len(win_streaks)}\n' + \
            f'\t\t[Len | Time]  = {win_streaks}\n' + \
            ('-' * 40 + '\n') + \
            'Result:\n' + \
            f'Starting balance = {ACCOUNT_BALANCE} USD\n' + \
            f'Ending balance   = {end_balance} USD\n' + \
            f'% result         = {(end_balance / ACCOUNT_BALANCE - 1) * 100} %\n' + \
            ('=' * 40 + '\n')
        return analysis_result
