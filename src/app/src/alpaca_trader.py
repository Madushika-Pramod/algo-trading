import asyncio
import json
import os

import websockets
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import TrailingStopOrderRequest

from app.src import constants
from app.src.voice_alert import voice_alert


def get_trade_updates():
    # Create a new loop for the current thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Now use this loop to run your async function
        loop.run_until_complete(alpaca_trade_updates_ws())
    finally:
        print("close alpaca_ws")
        loop.close()


async def alpaca_trade_updates_ws():
    async with websockets.connect(constants.trade_stream_wss) as ws:
        # Authenticate
        auth_data = {
            "action": "auth",
            "key": os.environ.get("API_KEY"),
            "secret": os.environ.get("SECRET_KEY")
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
            print(message)
            trade = json.loads(message)['data']
            if trade['event'] == 'new' or trade['event'] == 'accepted':
                constants.pending_order = trade['order']  # todo
                voice_alert(f"say a {trade['order']['side']} order is placed", 1)
                voice_alert("say placed", 1)
                print(
                    f"a {trade['order']['side']} order is placed at price {trade['order']['hwm']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

            elif trade['event'] == 'filled':
                constants.accepted_order = trade['order']
                voice_alert(f"say a {trade['order']['side']} order is executed", 1)
                voice_alert("say executed", 1)
                print(
                    f"a {trade['order']['side']} order is executed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

            elif trade['event'] == 'canceled':

                voice_alert(f"say a {trade['order']['side']} order is canceled", 1)
                voice_alert("say canceled", 1)
                print(
                    f"a {trade['order']['side']} order is canceled at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

            # q.put(message)


# asyncio.get_event_loop().run_until_complete(alpaca_ws())


def get_last_trade_from_sdk():
    client = StockHistoricalDataClient(api_key=os.environ.get("API_KEY"), secret_key=os.environ.get("SECRET_KEY"))
    request = StockLatestTradeRequest(symbol_or_symbols=constants.symbol)
    return client.get_stock_latest_trade(request)


class AlpacaTrader:
    def __init__(self):
        self.cash = constants.cash
        self.algo_price = None
        self.trading_client = TradingClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"), paper=True)

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
            print(f"algo price={self.algo_price} > current price={current_price} <=> price decreasing")
            return ""

        # execute new trailing stop order
        trailing_stop_order_data.qty = self._buy_quantity(current_price)
        if trailing_stop_order_data.qty > 0:
            return self.trading_client.submit_order(order_data=trailing_stop_order_data).id
        return ""

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

        if current_price > self.algo_price:  # price increasing
            print(f"algo price={self.algo_price} < current price={current_price} <=> price increasing")
            return ""

        # execute new trailing stop order
        if trailing_stop_order_data.qty > 0:
            return self.trading_client.submit_order(order_data=trailing_stop_order_data).id
        return ""

    def _buy_quantity(self, price):
        self.cash = self.trading_client.get_account().cash  # buying_power todo

        # Calculate maximum shares factoring in the commission
        return int(float(self.cash / (price + constants.commission)))