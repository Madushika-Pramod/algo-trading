import backtrader as bt
import pandas

import constants
# from app.src.alpaca_data import AlpacaHistoricalData
from app.src.trade_analyzer import TradeAnalyzer


# from .alpaca_data import AlpacaHistoricalData
# from .trade_analyzer import TradeAnalyzer


def load_data(file_path=constants.csv_file_path, noheaders=False, symbol=constants.symbol,
              period_in_days=constants.period_in_days):
    skip_rows = 1 if noheaders else 0
    header = None if noheaders else 0
    # if constants.data_download == 1:
    #     AlpacaHistoricalData(symbol, period_in_days,
    #                          file_path).save_to_csv()
    #     constants.data_download = 0

    df = pandas.read_csv(file_path,
                         skiprows=skip_rows,
                         header=header,
                         parse_dates=True)

    df['timestamp'] = pandas.to_datetime(df['timestamp'])
    df.set_index(df['timestamp'], inplace=True)

    return df


def back_test(strategies):
    for strategy in strategies:
        BacktraderStrategy(strategy).run()


class BacktraderStrategy:
    def __init__(self, strategy_class, cash=constants.cash, live=False):
        self.live = live
        self.cash = cash
        self.strategy_class = strategy_class
        self.cerebro = bt.Cerebro()
        if not live:
            self.df = load_data()
            self.add_historical_data()
            self.cerebro.addanalyzer(TradeAnalyzer, _name="trade_analyzer")
        self.cerebro.addstrategy(strategy_class)
        self.cerebro.broker.setcash(self.cash)

    def add_historical_data(self):
        data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.adddata(data)

    def run(self):
        if self.live:
            self.cerebro.run(live=True)
        else:
            strategies = self.cerebro.run()
            # self.cerebro.plot(style='candle')
            self.cerebro.plot()

            strat = strategies[0]  # gets the first (and in this case, only) strategy
            # Access the analyzer's results and print them
            analysis = strat.analyzers.trade_analyzer.get_analysis()
            print("\n\n<== Statistics for {} ==>".format(analysis["strategy"]))
            print('Trade Count: ', analysis["trade_count"])
            print('Win Count: ', analysis["win_count"])
            print('Loss Count: ', analysis["loss_count"])
            print('Win Rate: ', "{}%".format(round(analysis["win_rate"] * 100, 2)))
            print('ROI: ', analysis["total_roi"])
            print('Invest: ', analysis["invest"])
            print('Profit: ', analysis["profit"])
            print("<== ==End== ==>\n\n")
