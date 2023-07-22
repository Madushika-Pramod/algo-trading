import backtrader as bt
import numpy as np


class TrendLine(bt.Indicator):
    lines = ('slope_predicted', 'real_slope', 'predicted_curve',)
    params = dict(period=None, poly_degree=None, predicted_line_length=None, line_degree=None)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        slope_predicted=dict(_name='slope_predicted', _plotskip=False),
        real_slope=dict(_name='real_slope', _plotskip=False ),
        predicted_curve=dict(_name='predicted_curve', _plotskip=False),
    )

    def __init__(self):
        self.addminperiod(self.p.period)
        # self.adx = bt.ind.AverageDirectionalMovementIndex()

    def plotlabel(self):
        return 'TrendLine Indicator'

    def next(self):

        ys = self.data.get(size=self.p.period)
        xs = np.arange(len(ys))
        coefs = np.polyfit(xs, ys, self.p.poly_degree)

        if self.p.predicted_line_length % 2 != 0:
            # get nearest even number
            self.p.predicted_line_length -= 1

# here I'm going to get last values from predicted line and compare them with real line
# to do so, I get last points of predicted curve and plot them to get a line
# do then same for real curve

        # get x values for 2 lines
        x = np.array([x for x in range(self.p.predicted_line_length)])
        # this spans from the middle of the observed data ('ys') to the same length into the future.
        # Therefore, for a 'predicted_line_length' of L, it includes the last L/2 observed data points and predicts the next L/2 future data points.
        predicted_values = np.array([np.polyval(coefs, x) for x in
                                     range(len(ys) - int(self.p.predicted_line_length / 2),
                                           len(ys) + int(self.p.predicted_line_length / 2))])
        # This code retrieves the actual data values ('self.data') corresponding to the range used for prediction.
        # The range for actual data is determined by the 'predicted_line_length' parameter.
        # It starts from the point '- predicted_line_length + 1' from the end and goes up to the last data point in 'self.data' to get the same range as predicted_values
        real_values = np.array([self.data[x] for x in range(-1 * self.p.predicted_line_length + 1, 1)])

        predicted_slope = np.polyfit(x, predicted_values, self.p.line_degree)[0]
        real_slope = np.polyfit(x, real_values, self.p.line_degree)[0]

        self.lines.real_slope[0] = real_slope
        self.lines.slope_predicted[0] = predicted_slope
        self.lines.predicted_curve[0] = predicted_values[-1]  # Storing the last predicted value



class TrendLineStrategy(bt.Strategy):
    params = dict(
        period=None,
        poly_degree=None,
        predicted_line_length=None,
        line_degree=None,
        devfactor=2.0,
        b_band_period=2

    )

    def __init__(self):
        self.order = None
        self.trend_line = TrendLine(self.data, period=self.p.period, poly_degree=self.p.poly_degree,
                                    predicted_line_length=self.p.predicted_line_length, line_degree=self.p.line_degree)

        # add Bollinger Bands indicator and track the buy/sell signals
        self.b_band = bt.ind.BollingerBands(self.datas[0],
                                            period=self.p.b_band_period,
                                            devfactor=self.p.devfactor)
        self.b_band_buy_signal = bt.ind.CrossOver(self.datas[0],
                                                  self.b_band.lines.bot)
        self.b_band_sell_signal = bt.ind.CrossOver(self.datas[0],
                                                   self.b_band.lines.top)

        # self.sma_crossover = bt.ind.CrossOver(sma1, sma2)
        self.position_size = False  # if no buy orders

    def next(self):
        real_slope = self.trend_line.lines.real_slope[0]
        slope_predicted = self.trend_line.lines.slope_predicted[0]
        # todo improve with slope difference

        if self.position_size and real_slope > 0 > slope_predicted and 0 > self.b_band_sell_signal:
            self.sell()
            self.position_size = False

        elif not self.position_size and real_slope < 0 < slope_predicted and 0 < self.b_band_buy_signal:
            self.buy()
            self.position_size = True

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')  # Print date and log message

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None
