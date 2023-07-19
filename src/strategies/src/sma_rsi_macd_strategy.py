import backtrader as bt


class SmaRsiMacdStrategy(bt.Strategy):
    params = dict(
        sma_period=50,
        macd1=12,
        macd2=26,
        macdsig=9,
        rsi_period=14,
        rsi_lower=30,
        rsi_upper=70
    )

    def __init__(self):
        self.sma = bt.ind.MovingAverageSimple(
            self.data.close, period=self.params.sma_period
        )
        self.macd = bt.ind.MACD(
            self.data.close,
            period_me1=self.params.macd1,
            period_me2=self.params.macd2,
            period_signal=self.params.macdsig
        )
        self.rsi = bt.ind.RelativeStrengthIndex(
            self.data.close, period=self.params.rsi_period
        )
        self.order = None
        self.order_status = False

    def next(self):
        # If not in the market
        if not self.order_status:
            # Buy if RSI is below lower limit and MACD's macd line is above signal line and the closing price is above the SMA
            if self.rsi[0] < self.params.rsi_lower and self.macd.macd[0] > self.macd.signal[0] and self.data.close[0] > \
                    self.sma[0]:
                self.buy()

        # Already in the market
        else:
            # Sell if RSI is above upper limit and MACD's macd line is below signal line or the closing price is below the SMA
            if self.rsi[0] > self.params.rsi_upper and (
                    self.macd.macd[0] < self.macd.signal[0] or self.data.close[0] < self.sma[0]):
                self.sell()
