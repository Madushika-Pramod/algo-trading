import queue
from datetime import datetime, timezone, timedelta

import backtrader as bt
import pandas

from app.src import constants
from app.src.alpaca_data import AlpacaStreamData
# from app.src.alpaca_data import AlpacaHistoricalData
from app.src.trade_analyzer import TradeAnalyzer


# from .alpaca_data import AlpacaHistoricalData
# from .trade_analyzer import TradeAnalyzer
def generate_data():
    import random

    # Initialize synthetic data
    data = [
        ["symbol", "timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"],
        ["GOOGL", "2023-08-04 08:00:00+00:00", 129.4, 129.4, 129.4, 129.4, 432.0, 21.0, 129.371782]
    ]

    # Define the trend (increase or decrease)
    trend = "increase"

    # Generate data for 5000 data points
    for _ in range(5000):
        last_entry = data[-1]
        timestamp = datetime.fromisoformat(last_entry[1].split("+")[0]) + timedelta(minutes=1)

        if trend == "increase":
            change = round(random.uniform(0, 1), 2)
            trend = "decrease"
        else:
            change = round(-random.uniform(0, 2), 2)
            trend = "increase"

        new_open = round(last_entry[3] + change, 2)
        high = round(new_open + random.uniform(0, 0.5), 2)
        low = round(new_open - random.uniform(0, 0.5), 2)
        close = round((high + low) / 2, 2) -1

        volume = round(last_entry[6] * (1 + random.uniform(-0.05, 0.05)), 2)
        trade_count = round(last_entry[7] + random.choice([-1, 1]), 2)
        vwap = round((close * volume + last_entry[8] * last_entry[6]) / (volume + last_entry[6]), 2)

        data.append(["GOOGL", str(pandas.Timestamp(timestamp).tz_localize('UTC')), new_open, high, low, close, volume, trade_count, vwap])

    # Convert data to Pandas DataFrame
    df = pandas.DataFrame(data[1:], columns=data[0])
    # print(df.head())

    df['timestamp'] = pandas.to_datetime(df['timestamp'])
    df.set_index(df['timestamp'], inplace=True)

    return df


class AllInSizer(bt.Sizer):
    # params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # Divide all available cash by the closing price to get the number of shares we can buy
            size = int(cash / (data.close[0] * (1 + constants.commission)))
            print(f"Number of shares brought {size}")
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
    def __init__(self, live, cash=constants.cash, ):
        self.live = live
        self.cash = cash
        # self.strategy_class = strategy_class
        self.cerebro = bt.Cerebro()
        # simulating
        self.df = generate_data()  # DataHandler().load_data()
        # self.cerebro.cheat_on_close = True  # can execute Market orders on the close of the current bar
        self.cerebro.broker.setcommission(commission=constants.commission)
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

        # back testing end indicator todo optimize this
        q.put({'close': 0, 'high': 0, 'low': 0, 'open': 0,
               'timestamp': datetime(2023, 8, 10, 12, 0, 0, tzinfo=timezone.utc), 'trade count': 0, 'volume': 0,
               'vwap': 0})
        data = AlpacaStreamData(q=q)
        return data

    def add_strategy(self, strategy_with_params):
        strategy_class, params = strategy_with_params
        # if self.live:
        #     strategy_class = register_live_strategies.live_strategies.get(str(strategy_class))
        self.cerebro.addstrategy(strategy_class, **params)
        return self

    def run(self):

        if self.live:
            strategies = self.cerebro.run(live=True)
            # todo
        #     return 0.00
        # else:
        # startcash = self.cerebro.broker.getvalue()
        else:
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
        return strategies[0]

# DataHandler().load_data()

# strategy = (
#         SmaCrossStrategy,
#         dict(
#             fast_ma_period=19,
#             slow_ma_period=36,
#             high_low_period=16,
#             high_low_tolerance=0.3,
#             profit_threshold=1.0
#         ))
# score = BacktraderStrategy(live=True).add_strategy(strategy).run()
