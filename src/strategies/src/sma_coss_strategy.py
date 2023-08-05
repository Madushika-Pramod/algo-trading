import backtrader as bt

from app.src.constants import average_appl2, min_price


class SmaCrossStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(pfast=3, pslow=15, high_low_period=20, high_low_error=0.15, gain_value=2)

    def __init__(self):
        self.roi = None
        self.buy_comm = None
        self.buy_price = None
        self.start_cash = self.broker.get_cash()  # get initial cash
        self.realized_pnl = 0.0
        self.buy_status = False
        self.sell_status = False
        self.bought_price = None
        self.sold_price = None
        self.order_status = None
        sma1 = bt.ind.MovingAverageSimple(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.MovingAverageSimple(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        self.crossover.plotinfo.plot = False
        self.highest = bt.indicators.Highest(self.data.close, period=self.p.high_low_period)
        self.lowest = bt.indicators.Lowest(self.data.close, period=self.p.high_low_period)

        # self.sell_cont = 0
        # self.buy_count = 0

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')  # Print date and log message

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if order.isbuy():

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.log(f"Commission: {order.executed.comm}")
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
                # self.log(threading.current_thread().ident)
            elif order.issell():
                sell_price = order.executed.price

                self.realized_pnl += ((sell_price - self.buy_price) * abs(order.executed.size)) - self.buy_comm

                self.log('SELL EXECUTED, %.2f' % order.executed.price)
                # self.log(threading.current_thread().ident)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def stop(self):
        # calculate ROI
        self.roi = self.realized_pnl / self.start_cash
        # print('ROI: {:.3f}%'.format(100.0 * self.roi))

    def next(self):

        if self.order_status is False:  # not in the market
            if self.sold_price is not None and self.p.gain_value > self.sold_price - self.data.close[0]:
                return

            if self.data.close[0] - self.lowest[0] < self.p.high_low_error:
                self.buy_status = True
            else:
                self.buy_status = False

            if self.buy_status and self.data.volume[0] > average_appl2 and self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()
                self.buy_status = False
                self.order_status = True
                self.bought_price = self.data.close[0]
        elif self.order_status:  # in the market
            if self.p.gain_value > self.data.close[0] - self.bought_price:
                return
            if self.highest[0] - self.data.close[0] < self.p.high_low_error:
                self.sell_status = True
            else:
                self.sell_status = False

            if self.sell_status and self.data.volume[0] > average_appl2 and self.crossover < 0:  # in the market & cross to the downside
                self.sell()
                self.sell_status = False  # now it's a buy status
                self.order_status = False
                self.sold_price = self.data.close[0]
        elif self.order_status is None and self.data.close[0] < min_price:
            self.buy()
            self.buy_status = False
            self.order_status = True
            self.bought_price = self.data.close[0]
