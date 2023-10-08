import logging
import time

import backtrader as bt
import pytz
from alpaca.trading import OrderStatus

from broker.src.alpaca_crypto_trader import AlpacaCryptoTrader, CryptoDemoTrader
from strategies.src.indicators.talib_sma import TALibSMA


# todo if price is increasing we should stay
# todo if price is decreasing we should leave


class TrailingStopStrategy(bt.Strategy):
    params = dict(
        trail_percent_sell=3.0,
        trail_percent_buy=3.0,
        period=3,
        buying_power=800
    )

    def __init__(self):

        self.buy_limit_price = None
        self.buy_order = None
        self.sell_order = None
        self.sell_limit_price = None
        self.lwm = self.hwm = None
        self.stop_level = None

        self.win_count = 0
        self.loss_count = 0

        self.starting_buying_power = self.p.buying_power
        self.cumulative_profit = 0
        self.trading_count = 0
        self.roi = {}
        self.average_return_on_investment = 0
        self.order_quantity = None
        self.price_of_last_sale = None
        self.price_of_last_purchase = None
        self.trade_active = False
        self.live = None

        self.kama = bt.ind.KAMA(period=self.p.period)  # TALibSMA(period=self.p.period) SMMA

        self.trader = AlpacaCryptoTrader() if self.cerebro.params.live else CryptoDemoTrader(self.p.buying_power)

    # def start(self):
    #     self.lwm = self.hwm = self.data.close[0]
    #     self.order_quantity = self.starting_buying_power / self.data.close[0]
    #     self.price_of_last_sale = self.data.close[0]
    def buy_crypto(self):
        self.trade_active = True
        self.price_of_last_purchase = self.hwm = self.data.close[0]
        self.order_quantity = self.order_quantity * self.price_of_last_sale / self.data.close[0]
        self.notify_order(True)


    def sell_crypto(self):
        self.trade_active = False
        self.price_of_last_sale = self.lwm = self.data.close[0]
        self.notify_order(False)


    def trailing_stop_sell(self):
        self.hwm = max(self.hwm, self.data.close[0])
        self.stop_level = self.hwm  # * (1 - self.p.trail_percent_sell / 100.0)

    def trailing_stop_buy(self):
        # low watermark for `buy`
        self.lwm = min(self.lwm, self.data.close[0])
        self.stop_level = self.lwm  # * (1 + self.p.trail_percent_buy / 100.0)

    def _start_trade(self):
        if self.trade_active and self.sell_order is None:
            self._start_sell_process()
        elif self.buy_order is None:
            self._start_buy_process()

    def current_price_datetime(self):
        return bt.num2date(self.data.datetime[0]).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M:%S %p')

    def _start_sell_process(self):
        self.trailing_stop_sell()
        if self.data.close[0] < self.data.open[0] and self.data.close[0] <= self.kama[0] <= self.stop_level:
            self.sell_order = self.trader.sell(self.data.close[0])
            self.sell_limit_price = self.data.close[0]

    def _start_buy_process(self):
        self.trailing_stop_buy()
        if self.data.close[0] == self.data.high[0] and self.kama[0] >= self.stop_level:
            self.buy_order = self.trader.buy(self.data.close[0])
            self.buy_limit_price = self.data.close[0]

    def next(self):
        if self.order_quantity is None:
            self.order_quantity = self.trader.crypto_buying_power / self.data.close[0]
            self.lwm = self.hwm = self.price_of_last_sale = self.data.close[0]

        if self.buy_order is not None and self.trader.trading_client.get_order_by_id(
                self.buy_order).status == OrderStatus.FILLED:
            self.buy_crypto()
            self.buy_order = None
            self.buy_limit_price = None
        elif self.sell_order is not None and self.trader.trading_client.get_order_by_id(
                self.sell_order).status == OrderStatus.FILLED:
            self.sell_crypto()
            self.sell_order = None
            self.sell_limit_price = None

            #     if self.data.close[0] == 0:
        #         self.live = True
        #         self.order_quantity = None
        #
        #     elif self.live:
        #         print(f"close: {self.data.close[0]}")
        #
        #         self._start_trade()
        # else:
        self._start_trade()
        if self.cerebro.params.live:
            print(self.data.close[0])
            time.sleep(54)

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
