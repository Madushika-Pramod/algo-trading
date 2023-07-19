import backtrader as bt
import numpy as np


class TrendLine(bt.Indicator):
    lines = ('slope_predicted', 'slope_diff',)
    params = dict(period=None, poly_degree=None, predicted_line_length=None, line_degree=None)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        trend=dict(_name='slope_predicted'),
        slop_diff=dict(_name='slope_diff'),
    )

    def __init__(self):
        self.addminperiod(self.p.period)
        self.adx = bt.ind.AverageDirectionalMovementIndex()

    def plotlabel(self):
        return 'TrendLine Indicator'

    def next(self):
        ys = self.data.get(size=self.p.period)
        xs = np.arange(len(ys))
        coefs = np.polyfit(xs, ys, self.p.poly_degree)

        if self.p.predicted_line_length % 2 != 0:
            self.p.predicted_line_length -= 1

        x = np.array([x for x in range(self.p.predicted_line_length)])

        predicted_values = np.array([np.polyval(coefs, x) for x in
                                     range(len(ys) - int(self.p.predicted_line_length / 2),
                                           len(ys) + int(self.p.predicted_line_length / 2))])

        real_values = np.array([self.data[x] for x in range(-1 * self.p.predicted_line_length + 1, 1)])

        predicted_slope = np.polyfit(x, predicted_values, self.p.line_degree)[0]
        real_slope = np.polyfit(x, real_values, self.p.line_degree)[0]

        self.lines.slope_diff[0] = predicted_slope - real_slope
        self.lines.slope_predicted[0] = predicted_slope


class TrendLineStrategy(bt.Strategy):
    params = dict(
        fast=None,
        slow=None,
        period=None,
        poly_degree=None,
        predicted_line_length=None,
        line_degree=None,
        devfactor=2.0,
        b_band_period=2

    )

    def __init__(self):
        self.trend_line = TrendLine(self.data, period=self.p.period, poly_degree=self.p.poly_degree,
                                    predicted_line_length=self.p.predicted_line_length, line_degree=self.p.line_degree)

        sma1 = bt.ind.MovingAverageSimple(period=self.p.fast)  # fast moving average
        sma2 = bt.ind.MovingAverageSimple(period=self.p.slow)  # slow moving average
        # add Bollinger Bands indicator and track the buy/sell signals
        self.b_band = bt.ind.BollingerBands(self.datas[0],
                                            period=self.p.b_band_period,
                                            devfactor=self.p.devfactor)
        self.b_band_buy_signal = bt.ind.CrossOver(self.datas[0],
                                                  self.b_band.lines.bot)
        self.b_band_sell_signal = bt.ind.CrossOver(self.datas[0],
                                                   self.b_band.lines.top)

        self.sma_crossover = bt.ind.CrossOver(sma1, sma2)
        self.order = None
        self.position_size = False

    def next(self):
        slope_diff = self.trend_line.lines.slope_diff[0]
        slope_predicted = self.trend_line.lines.slope_predicted[0]

        if self.position_size and self.sma_crossover < 0 < slope_predicted < slope_diff and self.b_band_sell_signal < 0:
            self.sell()
            self.position_size = False

        elif not self.position_size and self.sma_crossover > 0 > slope_predicted > slope_diff and self.b_band_buy_signal > 0:
            self.order = self.buy()
            self.position_size = True

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        # print(f'{dt.isoformat()}, {txt}')  # Print date and log message

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None
