import asyncio
import os
import time

from alpaca.trading import OrderSide, TimeInForce, OrderStatus
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
            func(self.trading_client.get_account)).result().non_marginable_buying_power)  # since we did not await we should use results

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
                qty=(self.crypto_buying_power/price),
                limit_price=price,
            )
        order_id = asyncio.run(func(self.trading_client.submit_order(order_data=limit_order_data))).result().id
        self.update_buying_power()
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
            return order_id
        except:
            return None


class CryptoDemoTrader:
    def __init__(self, crypto_buying_power):
        self.crypto_buying_power = crypto_buying_power


    def buy(self):
        if not self.crypto_buying_power > 0:
            raise Exception("not enough buying power for crypto")
        return True

    def sell(self):
        return True


# x = AlpacaCryptoTrader()
# y = x.buy(8.165)
# g = x.trading_client.get_order_by_id(y.id)
# # y.status == OrderStatus.PENDING_NEW
# # time.sleep(5)
# v =4