import time

import backtrader as bt
import pytz

from broker.src.alpaca_crypto_trader import AlpacaCryptoTrader, CryptoDemoTrader
from strategies.src.indicators.talib_sma import TALibSMA


# todo if price is increasing we should stay
# todo if price is decreasing we should leave


class SmaStrategy(bt.Strategy):
    params = dict(

        slow_period=3,
        fast_period=4,
        profit_threshold=1,
        buying_power=800
    )

    def __init__(self):

        self.win_count = 0
        self.loss_count = 0

        self.price_of_last_purchase = None
        self.starting_buying_power = self.p.buying_power
        self.cumulative_profit = 0
        self.trading_count = 0
        self.roi = {}
        self.average_return_on_investment = 0
        self.order_quantity = None
        self.price_of_last_sale = None
        self.trade_active = False
        self.live = None

        self.slow_kama = TALibSMA(period=self.p.slow_period)
        self.fast_kama = TALibSMA(period=self.p.fast_period)

        self.trader = AlpacaCryptoTrader() if self.cerebro.params.live else CryptoDemoTrader(self.p.buying_power)

    def buy_crypto(self):
        self.trade_active = True
        self.price_of_last_purchase = self.data.close[0]
        self.order_quantity = self.order_quantity * self.price_of_last_sale / self.data.close[0]
        self.notify_order(True)

    def sell_crypto(self):
        self.trade_active = False
        self.price_of_last_sale = self.data.close[0]
        self.notify_order(False)

    def _start_trade(self):
        if self.trade_active:
            self._start_sell_process()
        else:
            self._start_buy_process()

    def current_price_datetime(self):
        return bt.num2date(self.data.datetime[0]).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M:%S %p')

    def _start_sell_process(self):
        if (self.data.close[0] == self.data.low[0] and self.slow_kama > self.fast_kama ) or self.data.close[
            0] <= 1.0005 * self.price_of_last_purchase:
            if self.trader.sell():
                self.sell_crypto()

    def _start_buy_process(self):
        if self.data.close[0] == self.data.high[0] and self.slow_kama < self.fast_kama:
            if self.trader.buy():
                self.buy_crypto()

    def next(self):

        if self.order_quantity is None:
            self.order_quantity = self.trader.crypto_buying_power / self.data.close[0]
            self.price_of_last_sale = self.data.close[0]
        self._start_trade()

        if self.cerebro.params.live:
            time.sleep(59)

    def stop(self):
        # print(f'win count: {self.win_count}\nloss count: {self.loss_count} ')
        if len(self.roi.values()) > 0:
            self.average_return_on_investment = sum(self.roi.values()) / len(self.roi.values())

    def log(self, txt, dt=None):
        """ Logging function for the strategy """
        dt = dt or self.current_price_datetime()
        # logging.info(f'{dt}, {txt}')

    def notify_order(self, is_buy_order):
        """Handle the events of executed orders."""

        if is_buy_order:
            # self.commission_on_last_purchase = order.executed.comm
            # self.log(f"Commission on Buy: {order.executed.comm}")
            # self.log('BUY EXECUTED, %.2f' % order.executed.price)  # executing.price for a buy is next bar's open price
            self.log('BUY EXECUTED, %.2f' % self.price_of_last_purchase)
        else:
            if self.price_of_last_sale - self.price_of_last_purchase < 0:
                self.loss_count += 1
            elif self.price_of_last_sale - self.price_of_last_purchase > 0:
                self.win_count += 1

            self.trading_count += 1
            self.cumulative_profit += (self.price_of_last_sale - self.price_of_last_purchase) * self.order_quantity

            roi = round(self.cumulative_profit / self.starting_buying_power, 3)
            self.roi[self.current_price_datetime()] = roi
            # logging.info(f"{roi * 100}%")

            self.log('SELL EXECUTED, %.2f with quantity of %.10f' % (
                self.price_of_last_sale, self.order_quantity))
