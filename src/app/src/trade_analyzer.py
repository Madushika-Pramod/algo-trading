from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt


class TradeAnalyzer(bt.Analyzer):

    def __init__(self):

        self.start_cash = self.strategy.broker.get_cash()
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.total_roi = 0.0
        self.profit = 0.0

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1

            if trade.pnl > 0:
                self.win_count += 1
            elif trade.pnl <= 0:
                self.loss_count += 1

    def stop(self):
        final_cash = self.strategy.broker.get_cash()
        self.total_roi = (final_cash - self.start_cash) / self.start_cash
        self.profit = final_cash - self.start_cash

    def get_analysis(self):
        win_rate = self.win_count / self.trade_count if self.trade_count else 0.0

        return {
            "strategy": str(self.strategy).split('.')[2],
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": win_rate,
            "total_roi": self.total_roi,
            "invest": self.start_cash,
            "profit": self.profit
        }
