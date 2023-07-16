import backtrader as bt
import numpy as np


class TrendLine(bt.Indicator):
    lines = ('trend', 'deviation',)  # added 'price' line
    params = (('period', None), ('degree', None))
    plotinfo = dict(subplot=False)
    plotlines = dict(
        trend=dict(_name='trend'),
        deviation=dict(_name='deviation'),
    )

    def __init__(self):
        self.addminperiod(self.params.period)

    def plotlabel(self):
        return 'TrendLine Indicator'

    def next(self):
        ys = self.data.get(size=self.params.period)
        xs = np.arange(len(ys))
        coefs = np.polyfit(xs, ys, self.params.degree)  # Fit polynomial of given degree
        trend_value = np.polyval(coefs, len(ys))
        self.lines.trend[0] = trend_value
        self.lines.deviation[0] = self.datas[0] - trend_value


class TrendLineStrategy(bt.Strategy):
    params = (('period', 30), ('degree', 2))

    def __init__(self):
        self.trend_line = TrendLine(self.data, period=self.params.period, degree=self.params.degree)

    def next(self):
        print('Price: %.2f, Trendline: %.2f, Deviation: %.2f' %
              (self.data[0], self.trend_line.lines.trend[0], self.trend_line.lines.deviation[0]))

    def stop(self):
        print('(Period %2d) Ending Value %.2f' %
              (self.params.period, self.broker.getvalue()))
