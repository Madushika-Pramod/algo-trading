import backtrader as bt
import pandas
import queue
import constants
from app.src.alpaca_data import AlpacaStreamData, AlpacaWebSocket
# from app.src.alpaca_data import AlpacaHistoricalData
from app.src.trade_analyzer import TradeAnalyzer
from strategies import BollingerRSIStrategy, SmaCrossStrategy


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
        # todo change here t => timestamp for python sdk
        # df['timestamp'] = pandas.to_datetime(df['t'])
        df['timestamp'] = pandas.to_datetime(df['timestamp'])
        df.set_index(df['timestamp'], inplace=True)
        # del df['t']

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
        self.df = DataHandler().load_data()
        if live:

            data = self._historical_and_live_data()
            self.cerebro.adddata(data)
            # self.cerebro.addanalyzer(TradeAnalyzer, _name="trade_analyzer")

        else:
            data = bt.feeds.PandasData(dataname=self.df)
            self.cerebro.adddata(data)
            self.cerebro.addanalyzer(TradeAnalyzer, _name="trade_analyzer")

        self.cerebro.broker.setcash(self.cash)
        self.cerebro.addsizer(AllInSizer)

    def _historical_and_live_data(self):
        q = queue.Queue()
        for row in self.df.to_dict(orient='records'):
            # Insert each row (a Series) into the queue
            row['timestamp'] = row['timestamp'].to_pydatetime()
            q.put(row)

        data = AlpacaStreamData(q=q)
        return data

    def add_strategy(self, strategy_with_params):
        strategy_class, params = strategy_with_params
        self.cerebro.addstrategy(strategy_class, **params)
        return self

    def run(self):
        self.cerebro.broker.setcommission(commission=0.005)
        if self.live:
            self.cerebro.run(live=True)
            # todo
            return 0.00
        else:
            # startcash = self.cerebro.broker.getvalue()

            strategies = self.cerebro.run()
            # endcash = self.cerebro.broker.getvalue()
            # roi = (endcash - startcash) / startcash

            # print('ROI not from strategy: {:.2f}%'.format(100.0 * roi))

            # self.cerebro.plot(style='candle')
            # self.cerebro.plot()
            # strat = strategies[0]
            # analysis = strat.analyzers.trade_analyzer.get_analysis()
            # display_statistics(analysis)
            # print("roi2:", strategies[0].roi2)
            return strategies[0].roi


def back_test(strategies):
    for strategy in strategies:
        BacktraderStrategy(strategy).run()

# DataHandler().load_data()

# strategy = (
#         SmaCrossStrategy,
#         dict(
#             pfast=2,  # 50 period for the fast moving average
#             pslow=23,  # 200 period for the slow moving average
#             high_low_period=8,
#             high_low_error=0.5,
#             gain_value=3.0
#         ))
# score = BacktraderStrategy(live=True).add_strategy(strategy).run()
# print(score)
