import backtrader as bt
import pandas

import constants
# from app.src.alpaca_data import AlpacaHistoricalData
from app.src.trade_analyzer import TradeAnalyzer


# from .alpaca_data import AlpacaHistoricalData
# from .trade_analyzer import TradeAnalyzer


class AllInSizer(bt.Sizer):
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # Divide all available cash by the closing price to get the number of shares we can buy
            size = cash // data.close[0]
        else:
            # If we're selling, sell all shares
            size = self.broker.getposition(data).size
        return size


class DataHandler:
    def __init__(self, file_path=constants.csv_file_path, noheaders=False, symbol=constants.symbol,
                 period_in_days=constants.period_in_days):
        self.file_path = file_path
        self.noheaders = noheaders
        self.symbol = symbol
        self.period_in_days = period_in_days

    def load_data(self):
        skip_rows = 1 if self.noheaders else 0
        header = None if self.noheaders else 0
        # if constants.data_download == 1:
        #     AlpacaHistoricalData(symbol, period_in_days,
        #                          file_path).save_to_csv()
        #     constants.data_download = 0

        df = pandas.read_csv(self.file_path,
                             skiprows=skip_rows,
                             header=header,
                             parse_dates=True)

        df['timestamp'] = pandas.to_datetime(df['timestamp'])
        df.set_index(df['timestamp'], inplace=True)

        return df


def display_statistics(analysis):
    print(f"\n\n<== Statistics for {analysis['strategy']} ==>")
    print('Trade Count: ', analysis["trade_count"])
    print('Win Count: ', analysis["win_count"])
    print('Loss Count: ', analysis["loss_count"])
    print('Win Rate: ', f"{round(analysis['win_rate'] * 100, 2)}%")
    print('ROI: ', analysis["total_roi"])
    print('Invest: ', analysis["invest"])
    print('Profit: ', analysis["profit"])
    print(f'Profit: {round(analysis["total_roi"] * 100, 2)}%')

    print("<== ==End== ==>\n\n")


class BacktraderStrategy:
    def __init__(self, cash=constants.cash, live=False):
        self.live = live
        self.cash = cash
        # self.strategy_class = strategy_class
        self.cerebro = bt.Cerebro()
        if not live:
            self.data_handler = DataHandler()
            self.df = self.data_handler.load_data()
            self._add_historical_data()
            self.cerebro.addanalyzer(TradeAnalyzer, _name="trade_analyzer")
        # self.cerebro.addstrategy(strategy_class, period=20, degree=3, fast=1, slow=20)
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.addsizer(AllInSizer)

    def add_strategy(self, strategy_with_params):
        strategy_class, params = strategy_with_params
        self.cerebro.addstrategy(strategy_class, **params)
        return self

    def _add_historical_data(self):
        data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.adddata(data)

    def run(self):
        # self.cerebro.broker.setcommission(commission=0.01)
        if self.live:
            self.cerebro.run(live=True)
            return 0.00
        else:
            strategies = self.cerebro.run()
            # self.cerebro.plot(style='candle')
            # self.cerebro.plot()
            strat = strategies[0]
            analysis = strat.analyzers.trade_analyzer.get_analysis()
            # display_statistics(analysis)
            return analysis["total_roi"]


def back_test(strategies):
    for strategy in strategies:
        BacktraderStrategy(strategy).run()
