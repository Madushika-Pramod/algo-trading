import logging

import backtrader as bt
import pytz

from strategies.src.indicators.talib_sma import TALibSMA


# todo if price is increasing we should stay
# todo if price is decreasing we should leave
class TrailingStopSellIndicator(bt.Indicator):
    lines = ('hwm', 'stop_level')
    params = (
        # ('trail_value', 0),  # The dollar value for trailing
        ('trail_percent', 0),  # The percent value for trailing

    )

    def __init__(self, kama):
        super().__init__()
        self.addminperiod(1)  # Require at least one period
        self.lines.hwm = self.data.close  # Initialize hwm with close price
        self.kama = kama


    def next(self):
        print(self.kama[0])
        # Calculate high watermark for `sell`
        self.lines.hwm[0] = max(self.lines.hwm[-1], self.kama[0])

        # Calculate stop level for sell
        # if self.trail_type == 'value':
        #     self.lines.stop_level[0] = self.lines.hwm[0] - self.p.trail_value
        # elif self.trail_type == 'percent':
        self.lines.stop_level[0] = self.lines.hwm[0] * (1 - self.p.trail_percent / 100.0)

class TrailingStopBuyIndicator(bt.Indicator):
    lines = ('lwm', 'stop_level')
    params = (
        # ('trail_value', 0),  # The dollar value for trailing
        ('trail_percent', 0),  # The percent value for trailing

    )

    def __init__(self, kama):
        super().__init__()
        self.addminperiod(1)  # Require at least one period
        # self.trail_type = 'value' if self.p.trail_value > 0 else 'percent'
        self.lines.lwm = self.data.close  # Initialize lwm with close price
        self.kama = kama


    def next(self):

        # low watermark for `buy`
        self.lines.lwm[0] = min(self.lines.lwm[-1], self.kama[0])

        # Calculate stop level for buy
        #     if self.trail_type == 'value':
        #         self.lines.stop_level[0] = self.lines.lwm[0] + self.p.trail_value
        #     elif self.trail_type == 'percent':
        self.lines.stop_level[0] = self.lines.lwm[0] * (1 + self.p.trail_percent / 100.0)


class TrailingStopStrategy(bt.Strategy):
    params = (
        # ('trail_value', 2.00),
        ('trail_percent', 1.0),
        ('period', 5)
    )

    def __init__(self):
        self.win_count = 0
        self.loss_count = 0
        self.starting_buying_power = 800
        self.cumulative_profit = 0
        self.trading_count = 0
        self.roi = {}
        self.total_return_on_investment = 0
        self.order_quantity = self.starting_buying_power / self.data.close[0]
        self.price_of_last_sale = self.data.close[0]
        self.trade_active = False

        self.kama = TALibSMA(period=self.p.period)
        self.sell_trail_stop_ind = TrailingStopSellIndicator(kama=self.kama,
            # trail_value=self.p.trail_value,
            trail_percent=self.p.trail_percent,

        )
        self.buy_trail_stop_ind = TrailingStopBuyIndicator(kama=self.kama,
            # trail_value=self.p.trail_value,
            trail_percent=self.p.trail_percent,
        )

    def _start_trade(self, buy, sell):
        # Initiate a buy if conditions are met
        if self.trade_active:
            self._start_sell_process(sell)
        else:
            self._start_buy_process(buy)
    def current_price_datetime(self):
        return bt.num2date(self.data.datetime[0]).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M:%S %p')

    def _start_sell_process(self, sell):
        self.sell_trail_stop_ind.prenext(self.kama[0])
        if self.kama[0] <= self.sell_trail_stop_ind.stop_level[0]:
            sell()

    def _start_buy_process(self, buy):
        self.buy_trail_stop_ind.prenext(self.kama[0])
        if self.kama[0] >= self.buy_trail_stop_ind.stop_level[0]:
            buy()

    # def prenext(self):

    def next(self):
        # # Your strategy logic here
        # # Example: Check if close price has crossed below the sell stop_level or above the buy stop_level
        # if self.data.close[0] <= self.sell_trail_stop_ind.stop_level[0]:
        #     print('Sell Stop Level Hit')
        #
        # if self.data.close[0] >= self.buy_trail_stop_ind.stop_level[0]:
        #     print('Buy Stop Level Hit')

        def buy():
            self.trade_active = True
            self.price_of_last_purchase = self.data.close[0]
            self.order_quantity = self.order_quantity * self.price_of_last_sale / self.data.close[0]
            self.notify_order(True)

        def sell():
            self.trade_active = False
            self.price_of_last_sale = self.data.close[0]
            self.notify_order(False)

        self._start_trade(buy, sell)

    def stop(self):
        print(f'win count: {self.win_count}\nloss count: {self.loss_count} ')
        if len(self.roi.values()) > 0:
            self.total_return_on_investment = max(self.roi.values())


    def log(self, txt, dt=None):
        """ Logging function for the strategy """
        dt = dt or self.current_price_datetime()
        logging.info(f'{dt}, {txt}')

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
            else:
                self.win_count += 1

            self.trading_count += 1
            self.cumulative_profit += (self.price_of_last_sale - self.price_of_last_purchase) * self.order_quantity
            self.roi[self.current_price_datetime()] = round(
                self.cumulative_profit / self.starting_buying_power, 3)

            self.log('SELL EXECUTED, %.2f with quantity of %.10f' % (
                self.price_of_last_sale, self.order_quantity))
