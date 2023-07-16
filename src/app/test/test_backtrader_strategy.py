import unittest

import pandas as pd

from BacktraderStrategy import BacktraderStrategy, load_data
from Strategies.AdvancedDualMomentumStrategy import AdvancedDualMomentumStrategy
from Strategies.AdvancedMovingAverageADXStrategy import AdvancedMovingAverageADXStrategy
from Strategies.BollingerRSIMeanReversion import BollingerRSIMeanReversion
from Strategies.SmaCrossStrategy import SmaCrossStrategy


class TestDataHandler(unittest.TestCase):
    def setUp(self):
        self.data = load_data('testData.txt')

    def test_load_data(self):
        self.assertIsInstance(self.data, pd.DataFrame)
        self.assertNotEqual(self.data.shape[0], 0)


class TestBacktraderStrategy(unittest.TestCase):
    def setUp(self):
        strategy_class = SmaCrossStrategy  # change as needed
        data_file_path = 'testData.txt'
        cash = 1000
        self.backtrader_strategy = BacktraderStrategy(strategy_class, file_path=data_file_path, cash=cash)

    def test_add_data(self):
        data_count = len(self.backtrader_strategy.cerebro.datas)
        self.assertEqual(data_count, 1)

    def test_broker_cash(self):
        self.assertEqual(self.backtrader_strategy.cerebro.broker.getvalue(), 1000)

    def test_run(self):
        profit = self.backtrader_strategy.run()
        self.assertIsInstance(profit, float)


# Strategies
class TestAdvancedMovingAverageADXStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = AdvancedMovingAverageADXStrategy
        self.csv_file_path = 'testData.txt'
        self.cash = 1000

    def test_ending_cash(self):
        strategy_instance = BacktraderStrategy(self.strategy, file_path=self.csv_file_path, cash=self.cash)
        strategy_instance.run()
        ending_cash = strategy_instance.cerebro.broker.getvalue()
        self.assertEqual(ending_cash, 1007.4300000000001)


class TestAdvancedDualMomentumStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy_class = AdvancedDualMomentumStrategy
        self.data_file_path = 'testData.txt'
        self.cash = 1000
        self.backtrader_strategy = BacktraderStrategy(self.strategy_class, file_path=self.data_file_path,
                                                      cash=self.cash)

    def test_run(self):
        self.backtrader_strategy.run()
        ending_cash = self.backtrader_strategy.cerebro.broker.getvalue()
        self.assertAlmostEqual(ending_cash, 997.56, places=2)


class TestBollingerRSIMeanReversionStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy_class = BollingerRSIMeanReversion
        self.data_file_path = 'testData.txt'
        self.cash = 1000
        self.backtrader_strategy = BacktraderStrategy(self.strategy_class, file_path=self.data_file_path,
                                                      cash=self.cash)

    def test_ending_cash(self):
        self.backtrader_strategy.run()
        ending_cash = self.backtrader_strategy.cerebro.broker.getvalue()
        expected_ending_cash = 999.05
        self.assertAlmostEqual(ending_cash, expected_ending_cash, delta=0.01,
                               msg="Ending cash does not match expected value.")


class TestBacktraderStrategyExecution(unittest.TestCase):
    def setUp(self):
        strategy_classes = [SmaCrossStrategy, AdvancedMovingAverageADXStrategy, BollingerRSIMeanReversion,
                            AdvancedDualMomentumStrategy]
        self.backtrader_strategies = [BacktraderStrategy(strategy, file_path='testData.txt', cash=1000) for strategy in
                                      strategy_classes]

    def test_order_rejections(self):
        for strategy in self.backtrader_strategies:
            strategy.run()
            rejected_orders = [order for order in strategy.cerebro.broker.orders if
                               order.status in [order.Rejected, order.Margin]]
            self.assertEqual(len(rejected_orders), 0, "Order Rejected/Margin for {}".format(strategy.strategy_class.__name__))



    def test_strategy_class(self):
        for strategy in self.backtrader_strategies:
            self.assertIn(strategy.strategy_class.__name__,
                          [SmaCrossStrategy.__name__, AdvancedMovingAverageADXStrategy.__name__,
                           BollingerRSIMeanReversion.__name__, AdvancedDualMomentumStrategy.__name__],
                          "Unexpected strategy class {}".format(strategy.strategy_class.__name__))
