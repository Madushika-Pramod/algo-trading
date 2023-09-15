import asyncio
import json
import logging
import os

import websockets
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest

from app.src import constants
from app.src.notify import news


# from app.src.voice_alert import voice_alert


def get_trade_updates(state):
    # Create a new loop for the current thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logging.info('Receiving alpaca trading updates')
        # Now use this loop to run your async function
        loop.run_until_complete(alpaca_trade_updates_ws(state))
    finally:
        logging.info("trading updates stopped")
        loop.close()


async def alpaca_trade_updates_ws(state):
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
            print(f'trade update: {message}')

        # Receive messages
        while True:
            message = await ws.recv()

            print(f'trade update: {message}')
            trade = json.loads(message)['data']

            # '''new: The order has been received by Alpaca, but not yet routed to the exchange.
            #    accepted: The order has been routed to the exchange, but not yet confirmed by the exchange.'''
            if trade['event'] == 'new':

                # voice_alert(f"say a {trade['order']['side']} order is placed", 1)
                # voice_alert("say placed", 1)
                print(f'new_order id:{trade["order"]["id"]}')  # tested
                logging.info(f'new_order id:{trade["order"]["id"]}')
                # logging.info(
                #     f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
                # news(
                #     f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            elif trade['event'] == 'accepted':

                state.accepted_order = trade['order']
                # voice_alert(f"say a {trade['order']['side']} order is placed", 1)
                # voice_alert("say placed", 1)
                print(f'accepted_order id:{state.accepted_order["id"]}')
                logging.info(f'accepted id:{state.accepted_order["id"]}')
                logging.info(
                    f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
                news(
                    f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")


            # '''partial_fill: The order has been partially executed by the exchange, meaning that some but not
            # all the requested quantity has been filled. fill: The order has been fully executed by the exchange,
            # meaning that all the requested quantity has been filled.'''
            elif trade['event'] == 'fill':

                state.filled_order = trade['order']
                print(f'filled_order id:{state.filled_order["id"]}')
                # voice_alert(f"say a {trade['order']['side']} order is executed", 1)
                # voice_alert("say executed", 1)
                logging.info(f'executed_order id:{state.filled_order["id"]}')
                logging.info(
                    f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
                news(
                    f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            elif trade['event'] == 'partial_fill':
                # voice_alert(f"say a {trade['order']['side']} order is executed", 1)
                # voice_alert("say executed", 1)
                logging.info(f'partial_fill_order id:{trade["order"]["id"]}')
                # logging.info(
                #     f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
                # news(
                #     f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

            # '''canceled: The order has been canceled by either the user or Alpaca, meaning that it will not be
            # executed. This could happen if the user requests to cancel the order, or if the order expires due to
            # its time in force parameter. '''
            elif trade['event'] == 'canceled':

                # voice_alert(f"say a {trade['order']['side']} order is canceled", 1)
                # voice_alert("say canceled", 1)
                logging.info(f'canceled_order id:{trade["order"]["id"]}')
                logging.info(
                    f"event type: {trade['event']}\na {trade['order']['side']} order is canceled at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
                # news(
                #     f"event type: {trade['event']}\na {trade['order']['side']} order is canceled at price {trade['order']['filled_avg_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            else:
                logging.info(
                    f"alpaca event > event type: {trade['event']}")
                news(f"alpaca event > event type: {trade['event']}")
            # q.put(message)


# asyncio.get_event_loop().run_until_complete(alpaca_ws())


def get_last_trade_from_sdk():
    client = StockHistoricalDataClient(api_key=os.environ.get("API_KEY"), secret_key=os.environ.get("SECRET_KEY"))
    request = StockLatestTradeRequest(symbol_or_symbols=constants.symbol)
    return client.get_stock_latest_trade(request)


def truncate_to_two_decimal(number):
    return int(round(number * 100, 2)) / 100.0


class AlpacaTrader:
    def __init__(self, trading_client=None):
        self.algo_price = None
        self.trading_client = trading_client or TradingClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"),
                                                              paper=True)

    async def fetch_account(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.trading_client.get_account)

    def get_buying_power(self):
        return float(asyncio.run(self.fetch_account()).buying_power)
        # bp = float(self.trading_client.get_account().buying_power)
        # return bp  # make this async

    def buy(self, price):
        self.algo_price = price

        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            trail_percent=0.1,
        )

        current_price = get_last_trade_from_sdk()[constants.symbol].price

        if current_price < self.algo_price:  # or self.account.daytrade_count == 3:  # price decreasing or day trade count reach
            logging.info(f"algo price={self.algo_price} > current price={current_price} <=> price decreasing")
            print('136')
            return ""

        # execute new trailing stop order
        trailing_stop_order_data.qty = self._buy_quantity(current_price)
        if trailing_stop_order_data.qty > 0:
            order = self.trading_client.submit_order(order_data=trailing_stop_order_data).id

            # todo add market order
            # if buying_power < current_price * trailing_stop_order_data.qty:
            #     try:
            #         _ = self.market_buy(notional=buying_power)
            #         constants.market_buy_order = True
            #     except:
            #         # todo check
            #         _ = self.market_buy(notional=truncate_to_two_decimal(buying_power))
            #         constants.market_buy_order = True
            # print('153') tested
            return order
        print('155')
        return ""

    # def market_order(self, price):
    #     #todo get pre-market bar data for improve this
    #
    #
    #     trailing_stop_order_data = Stop(
    #         symbol=constants.symbol,
    #         qty=self.trading_client.get_open_position(constants.symbol).qty,
    #         side=OrderSide.SELL,
    #         time_in_force=TimeInForce.DAY,
    #         trail_percent=0.1,
    #     )
    #
    #
    #     # execute new trailing stop order
    #     if trailing_stop_order_data.qty > 0:
    #         return self.trading_client.submit_order(order_data=trailing_stop_order_data).id
    #     return ""

    def market_buy(self, notional=0.0, extended_hours=False):
        if notional <= 0:
            return

        market_order_data = MarketOrderRequest(
            symbol=constants.symbol,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            notional=notional,
            extended_hours=extended_hours

        )
        return self.trading_client.submit_order(order_data=market_order_data)

    def market_sell(self, notional=0.0, extended_hours=False):
        if notional <= 0:
            return
        market_order_data = MarketOrderRequest(
            symbol=constants.symbol,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            notional=notional,
            extended_hours=extended_hours
        )
        return self.trading_client.submit_order(order_data=market_order_data)

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
            logging.info(f"algo price={self.algo_price} < current price={current_price} <=> price increasing")
            return ""
        # execute new trailing stop order
        if trailing_stop_order_data.qty > 0:
            # todo this is a repeat abstract this and make a common method for this
            order = self.trading_client.submit_order(order_data=trailing_stop_order_data).id
            # buying_power = float(self.account.buying_power)
            # if buying_power < current_price * trailing_stop_order_data.qty and not constants.market_buy_order:
            #     try:
            #         _ = self.market_sell(notional=buying_power)
            #     except:
            #         # todo check
            #         _ = self.market_sell(notional=truncate_to_two_decimal(buying_power))
            return order
        return ""

    def _buy_quantity(self, price):

        # Calculate maximum shares factoring in the commission
        return int(self.get_buying_power() / (price + constants.commission))
        # todo check this, when calling saved variable account.cash, all ways get new cash value

# t = AlpacaTrader()
# #
# stop_order_data = StopOrderRequest(
#     symbol=constants.symbol,
#     side=OrderSide.BUY,
#     time_in_force=TimeInForce.DAY,
#     qty=1,
#     stop_price=100,
#     extended_hours=True
# )
#
# limit_order_data = LimitOrderRequest(
#     symbol=constants.symbol,
#     side=OrderSide.BUY,
#     time_in_force=TimeInForce.DAY,
#     qty=1,
#     limit_price=200,
#     extended_hours=True
# )
# t.trading_client.submit_order(order_data=limit_order_data)
#

# get_trade_updates()
