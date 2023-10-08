import asyncio
import logging
import os
import time
from unittest import mock
from unittest.mock import MagicMock

from alpaca.trading import OrderSide, TimeInForce, OrderStatus, Order
from alpaca.trading import TradingClient
from alpaca.trading.requests import LimitOrderRequest


async def func(function):
    loop = asyncio.get_event_loop()
    # return await loop.run_in_executor(None, self.trading_client.get_account)
    return loop.run_in_executor(None, function)


class AlpacaCryptoTrader:
    def __init__(self):
        self.trading_client = TradingClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"), paper=True)
        self.crypto_buying_power = 0
        self.update_buying_power()

    def update_buying_power(self):
        self.crypto_buying_power = float(asyncio.run(
            func(
                self.trading_client.get_account)).result().non_marginable_buying_power)  # since we did not await we should use results

    def buy(self, price):

        if not self.crypto_buying_power > 0:
            raise Exception("not enough buying power for crypto")
        # market_order_data = MarketOrderRequest(
        #     symbol="LINK/USD",
        #     side=OrderSide.BUY,
        #     time_in_force=TimeInForce.GTC,
        #     notional=self.crypto_buying_power,
        # )
        limit_order_data = LimitOrderRequest(
            symbol="LINK/USD",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            qty=(self.crypto_buying_power / price),
            limit_price=price,
        )
        order_id = asyncio.run(func(self.trading_client.submit_order(order_data=limit_order_data))).result().id
        self.update_buying_power()
        print(f'buy-{price}')
        logging.info(f'buy-{price}')
        return order_id

    def sell(self, price):

        try:
            limit_order_data = LimitOrderRequest(
                symbol="LINK/USD",
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
                qty=(self.crypto_buying_power / price),
                limit_price=price,
            )
            order_id = asyncio.run(func(self.trading_client.submit_order(order_data=limit_order_data))).result().id
            self.update_buying_power()
            print(f'sell-{price}')
            logging.info(f'sell-{price}')
            return order_id
        except:
            return None


class CryptoDemoTrader:
    def __init__(self, crypto_buying_power):
        self.crypto_buying_power = crypto_buying_power
        self.trading_client = MagicMock()
        self.order = MagicMock()
        self.trading_client.get_order_by_id = MagicMock(return_value=self.order)

    def buy(self, price):
        if not self.crypto_buying_power > 0:
            raise Exception("not enough buying power for crypto")
        self.order.id = 'buyorder'
        self.order.status = OrderStatus.FILLED

        return 'buyorder'

    def sell(self, price):
        self.order.id = 'sellorder'
        self.order.status = OrderStatus.FILLED
        return 'sellorder'

# x = AlpacaCryptoTrader()
# y = x.buy(8.165)
# g = x.trading_client.get_order_by_id(y.id)
# # y.status == OrderStatus.PENDING_NEW
# # time.sleep(5)
# v =4
