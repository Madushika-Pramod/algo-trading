# from alpaca.data import
import json
import os

import requests
import websockets
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import TrailingStopOrderRequest

from app.src import constants

API_KEY = "PK167PR8HAC3D9G2XMLS"
API_SECRET = "by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA"
URL = "wss://paper-api.alpaca.markets/stream"  # Use the appropriate URL (paper or live)


async def alpaca_ws():
    async with websockets.connect(URL) as ws:
        # Authenticate
        auth_data = {
            "action": "auth",
            "key": API_KEY,
            "secret": API_SECRET
        }
        await ws.send(json.dumps(auth_data))

        # Listen to trade updates
        listen_data = {
            "action": "listen",
            "data": {
                "streams": ["trade_updates"]
            }
        }
        await ws.send(json.dumps(listen_data))

        for _ in range(2):
            message = await ws.recv()
            print(message)

        # Receive messages
        while True:
            message = await ws.recv()
            constants.GOOGLE_ORDER = True  # todo order id
            # q.put(message)


# asyncio.get_event_loop().run_until_complete(alpaca_ws())


class AlpacaTrader:
    def __init__(self, api_key=None, secret_key=None):
        # self.orders = []
        self.order_id = None
        self.algo_price = None
        self.trading_client = TradingClient(api_key or os.environ.get("API_KEY"),
                                            secret_key or os.environ.get("SECRET_KEY"), paper=True)
        # self.live = False

    # def buy(self):
    #     if self.live:
    #         self._buy()
    #
    # def sell(self):
    #     if self.live:
    #         self._sell()

    def buy(self, price):
        self.algo_price = price
        # preparing order data
        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            qty=self._buy_quantity(),
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            trail_percent=0.1,
        )
        current_price = self.get_last_trade_From_sdk()[constants.symbol].price

        if current_price > self.algo_price:  # price increasing
            return None
        # cancel any pending buys
        self.trading_client.cancel_order_by_id(self.order_id)
        # trailing stop order
        self.order_id = self.trading_client.submit_order(order_data=trailing_stop_order_data).id
        # self.orders.append(order.id)
        return self.order_id

    def sell(self, price):
        self.algo_price = price

        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            qty=self.trading_client.get_open_position(constants.symbol).qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            trail_percent=1,
        )

        # self.current_price = self.get_last_trade()['trade']['p']
        current_price = self.get_last_trade_From_sdk()[constants.symbol].price

        if current_price < self.algo_price:  # price decreasing
            return None
        # cancel any pending sells

        # trailing stop order
        order = self.trading_client.submit_order(order_data=trailing_stop_order_data)
        return order.id

    # def cancel_orders(self):
    #     for order_id in self.orders:
    #         self.trading_client.cancel_order_by_id(order_id)

    def _buy_quantity(self):

        cash = self.trading_client.get_account().buying_power
        # Calculate maximum shares factoring in the commission
        return int(float(cash) / (self.algo_price + constants.commission))

    def get_last_trade_From_sdk(self):
        client = StockHistoricalDataClient(api_key='PK167PR8HAC3D9G2XMLS',
                                           secret_key='by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA')
        request = StockLatestTradeRequest(symbol_or_symbols=constants.symbol)
        return client.get_stock_latest_trade(request)

    def get_last_trade(self):

        url = "https://data.alpaca.markets/v2/stocks/googl/trades/latest?feed=iex"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": "PK167PR8HAC3D9G2XMLS",
            "APCA-API-SECRET-KEY": "by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA"
        }

        response = requests.get(url, headers=headers)

        return response.json()


# asyncio.get_event_loop().run_until_complete(alpaca_ws())

# trader = AlpacaTrader(api_key='PK167PR8HAC3D9G2XMLS', secret_key='by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA')
# print(trader.buy(132))

# v = trader.get_last_trade()
# x = trader.get_last_trade_From_sdk()
c = 2
