# import threading
import threading

import backtrader as bt

from app.src.constants import average_volume


# Create a Strategy
class BollingerRSIStrategy(bt.Strategy):
    params = dict(bbperiod=20, bbdev=2, rsiperiod=14, rsi_low=30, rsi_high=70, gain_value=1)

    def __init__(self):
        self.roi = None
        self.buy_comm = None
        self.buy_price = None
        self.start_cash = self.broker.get_cash()  # get initial cash
        self.realized_pnl = 0.0
        self.buy_status = None
        self.sell_status = False
        self.bought_price = None
        self.sold_price = None
        self.order_status = False
        self.bband = bt.indicators.BollingerBands(period=self.p.bbperiod, devfactor=self.p.bbdev)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.p.rsiperiod)
        self.previous_low = None
        self.previous_high = None
        self.waiting_for_rsi_to_come_back_up = False
        self.waiting_for_rsi_to_come_back_down = False
        # This typically signifies that the price was previously below the lower Bollinger Band (potentially
        # indicating an oversold condition), and now it has moved back up above the lower band. This crossover could
        # potentially indicate a reversal, suggesting that it might be a good time to buy.
        self.b_band_buy_signal = bt.indicators.CrossOver(self.data.close, self.bband.lines.bot)
        self.b_band_sell_signal = bt.indicators.CrossOver(self.data.close, self.bband.lines.top)

        # self.highest = bt.indicators.Highest(self.data.close, period=self.params.period)
        # self.lowest = bt.indicators.Lowest(self.data.close, period=self.params.period)

    def next(self):

        # highest_high = self.highest[0]
        # lowest_low = self.lowest[0]

        # if not self.position:
        # todo write using single if statement with and
        if not self.order_status:  # not in the market
            if self.sold_price is None or self.p.gain_value < self.sold_price - self.data.close[0]:

                if self.b_band_buy_signal > 0 or self.b_band_sell_signal > 0:
                    self.buy_status = True
                elif self.b_band_buy_signal < 0 or self.b_band_sell_signal < 0:
                    self.buy_status = False

                if self.buy_status:  # Cross above lower Bollinger Band
                    # todo real time data don't have data.low'
                    if self.previous_low is None or self.data.low[0] > self.previous_low:  # Higher low
                        if self.rsi[0] < self.p.rsi_low:
                            self.waiting_for_rsi_to_come_back_up = True
                        elif self.waiting_for_rsi_to_come_back_up and self.rsi[0] > self.p.rsi_low:
                            if self.data.volume[0] > average_volume:
                                self.buy()

                                self.buy_status = False
                                self.waiting_for_rsi_to_come_back_up = False
                                self.order_status = True
                                self.bought_price = self.data.close[0]
                self.previous_low = self.data.low[0]
        elif self.order_status:  # in the market
            if self.p.gain_value > self.data.close[0] - self.bought_price:
                return
            if self.b_band_sell_signal < 0 or self.b_band_buy_signal < 0:
                self.sell_status = True
            elif self.b_band_sell_signal > 0 or self.b_band_buy_signal > 0:
                self.sell_status = False
            if self.sell_status:  # Cross below upper Bollinger Band
                if self.previous_high is None or self.data.high[0] < self.previous_high:  # Lower high
                    if self.rsi[0] > self.p.rsi_high:
                        self.waiting_for_rsi_to_come_back_down = True
                    elif self.waiting_for_rsi_to_come_back_down and self.rsi[0] < self.p.rsi_high:
                        if self.data.volume[0] > average_volume:
                            self.sell()
                            self.sell_status = False  # now it's a buy status
                            self.waiting_for_rsi_to_come_back_down = False
                            self.order_status = False
                            self.sold_price = self.data.close[0]
            self.previous_high = self.data.high[0]
        # else:
        #     if self.buy_status is None and self.order_status is None and self.data.close[0] < min_price:
        #         self.buy()
        #         self.buy_status = False
        #         self.order_status = True
        #         self.bought_price = self.data.close[0]

    def stop(self):
        # calculate ROI
        self.roi = self.realized_pnl / self.start_cash
        # print('ROI: {:.3f}%'.format(100.0 * self.roi))

    def log(self, txt, dt=None):
        # ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')  # Print date and log message

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if order.isbuy():

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.log(f"Commission: {order.executed.comm}")
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
                self.log(threading.current_thread().ident)
            elif order.issell():
                sell_price = order.executed.price

                self.realized_pnl += ((sell_price - self.buy_price) * abs(order.executed.size)) - self.buy_comm

                self.log('SELL EXECUTED, %.2f' % order.executed.price)
                self.log(threading.current_thread().ident)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

# if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
#     if order in self.pending_orders:
#         self.pending_orders.remove(order)
