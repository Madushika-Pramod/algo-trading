import asyncio
import os

from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading import TradingClient
from alpaca.trading.requests import MarketOrderRequest

from app.src import constants


class AlpacaCryptoTrader:
    def __init__(self):
        self.trading_client = TradingClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"), paper=True)
        self.crypto_buying_power = 0
        self.update_buying_power()

    async def fetch_account(self):
        loop = asyncio.get_event_loop()
        # return await loop.run_in_executor(None, self.trading_client.get_account)
        return loop.run_in_executor(None, self.trading_client.get_account)

    def update_buying_power(self):
        self.crypto_buying_power = float(asyncio.run(self.fetch_account()).result().non_marginable_buying_power)  # since we did not await we should use results

    def buy(self):

        if not self.crypto_buying_power > 0:
            raise Exception("not enough buying power for crypto")
        market_order_data = MarketOrderRequest(
            symbol="LINK/USD",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            notional=self.crypto_buying_power,
        )
        self.trading_client.submit_order(order_data=market_order_data)
        return True

    def sell(self):

        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            self.update_buying_power()
            return True
        except:
            return False
