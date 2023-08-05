import backtrader as bt


class SmaRsiMacdStrategy(bt.Strategy):
    params = dict(
        sma_period=50,
        macd1=12,
        macd2=26,
        macdsig=9,
        rsi_period=14,
        rsi_lower=30,
        rsi_upper=70,
        stop_loss=0.02,  # 2% stop loss
        take_profit=0.06,  # 6% take profit
        printlog=True  # enable printing of log
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.data.datetime[0]
            if isinstance(dt, float):
                dt = bt.num2date(dt)
            print(f'{dt.isoformat()}, {txt}')  # Print date and close price

    def __init__(self):
        self.sma = bt.ind.MovingAverageSimple(self.data.close, period=self.params.sma_period)
        self.macd = bt.ind.MACD(self.data.close, period_me1=self.params.macd1, period_me2=self.params.macd2,
                                period_signal=self.params.macdsig)
        self.rsi = bt.ind.RelativeStrengthIndex(self.data.close, period=self.params.rsi_period)

        self.order = None  # To keep track of pending orders
        self.order_status = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset order status
        self.order = None

    def next(self):
        # # Do not continue if an order is pending
        # if self.order:
        #     return

        # If not in the market
        if not self.order_status:
            # Buy if RSI is below lower limit and MACD's macd line is above signal line and the closing price is above the SMA
            if self.rsi[0] < self.params.rsi_lower and self.macd.macd[0] > self.macd.signal[0] and self.data.close[0] > self.sma[0]:
                self.log(f'BUY CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.buy()
                self.order_status = True

        # Already in the market
        else:
            # Sell if RSI is above upper limit and MACD's macd line is below signal line or the closing price is below the SMA
            if self.rsi[0] > self.params.rsi_upper and (
                    self.macd.macd[0] < self.macd.signal[0] or self.data.close[0] < self.sma[0]):
                self.log(f'SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell()
                self.order_status = False

    def stop(self):
        self.log(
            f'(SMA Period {self.params.sma_period}) (MACD Period {self.params.macd1}, {self.params.macd2}, {self.params.macdsig}) (RSI Period {self.params.rsi_period}) Ending Value {self.broker.getvalue():.2f}',
            doprint=True)
