import unittest
from unittest.mock import patch, Mock, MagicMock, create_autospec

from alpaca.data import Trade
from alpaca.trading import TradeAccount, Order, Position

import broker
from app.src import constants
from broker.src.alpaca_trader import truncate_to_two_decimal, AlpacaTrader, get_last_trade_from_sdk


class TestAlpacaTrader(unittest.TestCase):
    def setUp(self):
        # Mocking required objects
        self.trading_client = MagicMock()
        self.trader = AlpacaTrader(trading_client=MagicMock())


    def test_truncate_to_two_decimal(self):
        self.assertEqual(truncate_to_two_decimal(5.676), 5.67)
        self.assertEqual(truncate_to_two_decimal(5.679), 5.67)
        self.assertEqual(truncate_to_two_decimal(5.1), 5.10)

    def test_buy(self):
        trade = create_autospec(Trade)
        trade.price = 90
        broker.src.alpaca_trader.get_last_trade_from_sdk = MagicMock(return_value={constants.symbol: trade})

        self.assertEqual(self.trader.buy(99), "")

        account = create_autospec(TradeAccount)
        account.buying_power = 1000
        self.trader.trading_client.get_account = MagicMock(return_value=account)
        order = create_autospec(Order)
        order.id = 123456
        self.trader.trading_client.submit_order = MagicMock(return_value=order)
        trade.price = 100

        self.assertEqual(self.trader.buy(99), order.id)

    def test_sell(self):
        trade = create_autospec(Trade)
        trade.price = 100
        broker.src.alpaca_trader.get_last_trade_from_sdk = MagicMock(return_value={constants.symbol: trade})

        self.assertEqual(self.trader.sell(99), "")

        self.trader.get_buying_power = MagicMock(return_value=1000)
        order = create_autospec(Order)
        order.id = 123456
        self.trader.trading_client.submit_order = MagicMock(return_value=order)
        position = create_autospec(Position)
        position.qty = 5
        self.trader.trading_client.get_open_position = MagicMock(return_value=position)
        trade.price = 90

        self.assertEqual(self.trader.sell(99), order.id)



if __name__ == '__main__':
    unittest.main()
