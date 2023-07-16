import time
import unittest

import backtrader as bt

from AlpacaData import AlpacaStreamData
from BacktraderStrategy import BacktraderStrategy

mock_data_formats = [
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:19:57.72912Z",
            "x": "V",
            "p": 188.05,
            "s": 90,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:29:23.729124Z",
            "x": "V",
            "p": 188.05,
            "s": 120,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:53:36.72912Z",
            "x": "V",
            "p": 188.05,
            "s": 870,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:53:42.7291Z",
            "x": "V",
            "p": 200,
            "s": 870,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:54:09.729124241Z",
            "x": "V",
            "p": 188.05,
            "s": 200,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:56:09.7296986924241Z",
            "x": "V",
            "p": 188.05,
            "s": 204,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:57:18.72Z",
            "x": "V",
            "p": 169.05,
            "s": 280,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    },
    {
        "symbol": "AAPL",
        "trade": {
            "t": "2023-07-11T19:58:25.728089124241Z",
            "x": "V",
            "p": 198.05,
            "s": 450,
            "c": [
                "@"
            ],
            "i": 7970,
            "z": "C"
        }
    }

]


class TestDemo(bt.Strategy):
    def __init__(self):
        self.order = None
        self.buy_counter = 0
        self.sell_counter = 0
        self.tick_volumes = []

    def next(self):
        self.tick_volumes.append([self.data.tick_volume, self.data.tick_open])
        if self.order is None:
            self.close()
            self.order = self.buy()
            self.buy_counter += 1
        else:
            self.close()
            self.sell()
            self.sell_counter += 1
        print("buy:" + str(self.buy_counter))
        print("sell:" + str(self.sell_counter))


class TestAlpacaStreamData(AlpacaStreamData):
    def run(self):
        for data in mock_data_formats:
            self.p.q.put(data)
            # time.sleep(0.35)  # delay for 0.35 seconds
            time.sleep(self.time_for_rate_limit)


# def mock_alpaca_stream_data_run(self):
#     mock_data_formats = [
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.729124241Z", "x": "V", "p": 188.05, "s": 200, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.72912Z", "x": "V", "p": 188.05, "s": 870, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.7296986924241Z", "x": "V", "p": 188.05, "s": 204, "c": ["@"],
#                    "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.72Z", "x": "V", "p": 169.05, "s": 280, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.728089124241Z", "x": "V", "p": 198.05, "s": 450, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.7291Z", "x": "V", "p": 200, "s": 870, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.729124Z", "x": "V", "p": 188.05, "s": 120, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#         {"symbol": "AAPL",
#          "trade": {"t": "2023-07-11T19:59:59.72912Z", "x": "V", "p": 188.05, "s": 90, "c": ["@"], "i": 7970,
#                    "z": "C"}},
#
#     ]
#
#     for data in mock_data_formats:
#         self.p.q.put(data)
#         # time.sleep(0.35)  # delay for 0.35 seconds
#         time.sleep(self.time_for_rate_limit)


class TestDemoStrategy(unittest.TestCase):
    # @patch.object(AlpacaStreamData, 'run', new=mock_alpaca_stream_data_run)
    def setUp(self):
        self.strategy = TestDemo
        self.backtrader_strategy = BacktraderStrategy(self.strategy, live=True)

        self.data = TestAlpacaStreamData()
        # self.data.start()
        self.backtrader_strategy.cerebro.adddata(self.data)

    def test_buy_and_sell_methods(self):
        # self.setUp_AlpacaStreamData()
        self.backtrader_strategy.cerebro.run(live=True)

        # The strategy is now run. We can check its orders:
        strats = self.backtrader_strategy.cerebro.runstrats[0]
        s = strats[0]

        # Check if any buy orders were issued:
        buy_orders = [order for order in s._orders if order.isbuy()]
        self.assertEqual(len(buy_orders), 18, "No buy orders were issued")

        # Check if any sell orders were issued:
        sell_orders = [order for order in s._orders if order.issell()]
        self.assertEqual(len(sell_orders), 21, "No sell orders were issued")

    def test_next_method_execution(self):
        strats = self.backtrader_strategy.cerebro.run(live=True)
        demo_strat = strats[0]  # extract the strategy instance
        # Checking if next was called at least once
        self.assertGreater(demo_strat.sell_counter, 0, "sell() was not called")
        self.assertGreater(demo_strat.buy_counter, 0, "buy() was not called")
        for i, (item1, item2) in enumerate(zip(mock_data_formats, demo_strat.tick_volumes)):
            self.assertEqual(item1["trade"]["s"], int(item2[0]), f"The volumes at index {i} are not equal")
            self.assertEqual(item1["trade"]["p"], item2[1], f"The prices at index {i} are not equal")
