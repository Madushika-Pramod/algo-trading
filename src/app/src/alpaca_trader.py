import json
import os

import websockets
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import TrailingStopOrderRequest

from app.src import constants

API_KEY = "PK167PR8HAC3D9G2XMLS"
API_SECRET = "by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA"


async def alpaca_trade_ws():
    async with websockets.connect(constants.trade_stream_wss) as ws:
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
            trade = json.loads(message)['data']
            if trade['event'] == 'new':
                print(f"Order created: id={trade['order']['id']}")
            elif trade['event'] == 'accepted':
                constants.GOOGLE_ORDER = trade['order']['id']
                print(f"Order created: id={constants.GOOGLE_ORDER}")

            # q.put(message)


# asyncio.get_event_loop().run_until_complete(alpaca_ws())


def get_last_trade_from_sdk():
    client = StockHistoricalDataClient(api_key='PK167PR8HAC3D9G2XMLS',
                                       secret_key='by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA')
    request = StockLatestTradeRequest(symbol_or_symbols=constants.symbol)
    return client.get_stock_latest_trade(request)


class AlpacaTrader:
    def __init__(self, api_key=None, secret_key=None):
        self.order_id = None
        self.algo_price = None
        self.trading_client = TradingClient(api_key or os.environ.get("API_KEY"),
                                            secret_key or os.environ.get("SECRET_KEY"), paper=True)

    def buy(self, price):
        self.algo_price = price
        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            trail_percent=0.1,
        )
        current_price = get_last_trade_from_sdk()[constants.symbol].price

        if current_price < self.algo_price:  # price decreasing
            return None
        # cancel any pending buys because they have not been executed
        print(f"algo price={self.algo_price} <=> current price={current_price}")
        if self.order_id is not None:
            # todo update/ replace without cancel
            self.trading_client.cancel_order_by_id(self.order_id)
        # execute new trailing stop order
        trailing_stop_order_data.qty = self._buy_quantity(current_price)
        if trailing_stop_order_data.qty > 0:
            self.order_id = self.trading_client.submit_order(order_data=trailing_stop_order_data).id
            # self.orders.append(order.id)
            return self.order_id
        return None

    def sell(self, price):
        self.algo_price = price

        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            qty=self.trading_client.get_open_position(constants.symbol).qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            trail_percent=0.1,
        )

        current_price = get_last_trade_from_sdk()[constants.symbol].price

        if current_price < self.algo_price:  # price decreasing
            return None
        # cancel any pending sells because they have not been executed
        if self.order_id is not None:
            self.trading_client.cancel_order_by_id(self.order_id)

        # execute new trailing stop order
        self.order_id = self.trading_client.submit_order(order_data=trailing_stop_order_data).id
        print("sell order placed")
        return self.order_id

    def _buy_quantity(self, price):

        cash = self.trading_client.get_account().buying_power
        # Calculate maximum shares factoring in the commission
        return int(float(cash) / (price + constants.commission))

# asyncio.get_event_loop().run_until_complete(alpaca_ws())

# trader = AlpacaTrader(api_key='PK167PR8HAC3D9G2XMLS', secret_key='by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA')
# print(trader.buy(132))

# v = trader.get_last_trade()
# x = trader.get_last_trade_From_sdk()
# c = 2
