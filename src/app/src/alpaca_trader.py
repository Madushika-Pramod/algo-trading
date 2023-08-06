import os

from alpaca.trading import OrderSide, TimeInForce
from alpaca.trading.client import TradingClient
from alpaca.data import CLi
from alpaca.trading.requests import TrailingStopOrderRequest

from app.src import constants


# from alpaca.data import


class AlpacaTrader:
    def __init__(self, api_key=None, secret_key=None):
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
        self.current_price = self.trading_client..get(
            f"https://data.alpaca.markets/v2/stocks/{constants.symbol}/trades/latest")

        if self.current_price > self.algo_price:  # price increasing
            return False
        #cancel any pending buys

        # trailing stop order
        self.trading_client.submit_order(order_data=trailing_stop_order_data)
        return True

    def _sell(self, price):
        # preparing order data
        self.algo_price = price
        """
symbol – The symbol identifier for the asset being traded
qty – The number of shares to trade. Fractional qty for stocks only with market orders.
notional – The base currency value of the shares to trade. For stocks, only works with MarketOrders. Does not work with qty.
side – Whether the order will buy or sell the asset.
type – The execution logic type of the order (market, limit, etc).
time_in_force – The expiration logic of the order.
extended_hours – Whether the order can be executed during regular market hours.
client_order_id – A string to identify which client submitted the order.
order_class – The class of the order. Simple orders have no other legs.
take_profit – For orders with multiple legs, an order to exit a profitable trade.
stop_loss – For orders with multiple legs, an order to exit a losing trade.
trail_price – The absolute price difference by which the trailing stop will trail.
trail_percent – The percent price difference by which the trailing stop will trail."""

        #cancel any pending sells
        trailing_stop_order_data = TrailingStopOrderRequest(
            symbol=constants.symbol,
            # qty=self._quantity(price),
            national=self._national_buy(),
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            trail_percent=1,
        )

        # ..automethod:: alpaca.data.historical.stock.StockHistoricalDataClient.get_stock_latest_trade
        # ..autoclass:: alpaca.data.requests.StockLatestTradeRequest

        self.current_price = self.trading_client.get(
            f"https://data.alpaca.markets/v2/stocks/{constants.symbol}/trades/latest")

        if self.current_price < self.algo_price:  # price decreasing
            return False

        # trailing stop order
        self.trading_client.submit_order(order_data=trailing_stop_order_data)
        return True

    def _buy_quantity(self):
        cash = self.trading_client.get_account().cash

        # Calculate maximum shares factoring in the commission
        return int(float(cash) / (self.algo_price + constants.commission))

    def _sell_quantity(self, price):

        return len(self.trading_client.get_all_positions())

    def _national_buy(self):
        return self.trading_client.get_account().cash

    def _national_sell(self):
        return self.trading_client.get_account().long_market_value
        # positions = self.trading_client.get_all_positions()
        # return sum(float(position.market_value) for position in positions)


trader = AlpacaTrader(api_key='PK167PR8HAC3D9G2XMLS',secret_key='by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA')
# trader.trading_client.get_account()


v = trader.buy(131.3)
c=2
