import backtrader as bt


# Create a Strategy
class BollingerRSIStrategy(bt.Strategy):
    params = dict(bbperiod=20, bbdev=2, rsiperiod=14, rsi_low=30, rsi_high=70, gain_value=1)

    def __init__(self):

        self.order = None
        self.bought_price = None
        self.order_status = False
        self.bband = bt.indicators.BollingerBands(period=self.p.bbperiod, devfactor=self.p.bbdev)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.p.rsiperiod)
        self.previous_low = None
        self.previous_high = None
        self.waiting_for_rsi_to_come_back_up = False
        self.waiting_for_rsi_to_come_back_down = False

        self.b_band_buy_signal = bt.indicators.CrossOver(self.data.close, self.bband.lines.bot)
        self.b_band_sell_signal = bt.indicators.CrossOver(self.data.close, self.bband.lines.top)

    def next(self):
        # if not self.position:
        if not self.order_status:  # not in the market
            if self.b_band_buy_signal > 0:  # Cross above lower Bollinger Band
                if self.data.low[0] > self.previous_low if self.previous_low else False:  # Higher low
                    if self.rsi[0] < self.p.rsi_low:
                        self.waiting_for_rsi_to_come_back_up = True
                    elif self.waiting_for_rsi_to_come_back_up and self.rsi[0] > self.p.rsi_low:
                        self.buy()
                        self.waiting_for_rsi_to_come_back_up = False
                        self.order_status = True
                        self.bought_price = self.data.close[0]
                self.previous_low = self.data.low[0]
        else:  # in the market
            if self.b_band_sell_signal < 0:  # Cross below upper Bollinger Band
                if self.data.high[0] < self.previous_high if self.previous_high else False:  # Lower high
                    if self.rsi[0] > self.p.rsi_high:
                        self.waiting_for_rsi_to_come_back_down = True
                    elif self.waiting_for_rsi_to_come_back_down and self.rsi[0] < self.p.rsi_high:
                        if self.data.close[0] - self.bought_price > self.p.gain_value:
                            self.sell()
                            self.waiting_for_rsi_to_come_back_down = False
                            self.order_status = False
                self.previous_high = self.data.high[0]

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
