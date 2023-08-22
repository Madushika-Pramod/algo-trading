from collections import deque

import backtrader as bt
import numpy as np
import pandas
import talib as TA


class MAMAIndicator(bt.Indicator):
    lines = ('mama', 'fama')
    params = dict(period=35)

    def __init__(self):
        self.addminperiod(self.p.period)
        self.last_N_prices = deque(maxlen=self.p.period)  # Use a deque to keep the last N prices

    def next(self):
        # Append the current close price to the deque
        self.last_N_prices.append(self.data.close[0])

        # Convert the deque to a numpy array
        data_series = np.array(self.last_N_prices)

        df = pandas.DataFrame({
            'open': data_series,
            'close': data_series,
            'high': data_series,
            'low': data_series
        })

        # Then, use the DataFrame for TA.MAMA
        mama, fama = TA.MAMA(df['close'].values)

        # Set current values for the indicator lines
        if len(mama) != 0 and mama[-1] is not None:
            self.lines.mama[0] = mama[-1]
        else:
            self.lines.mama[0] = float('nan')

        if len(fama) != 0 and fama[-1] is not None:
            self.lines.fama[0] = fama[-1]
        else:
            self.lines.fama[0] = float('nan')


# Then you can use the MAMAIndicator like any other indicator in Backtrader
class TestStrategy(bt.Strategy):
    def __init__(self):
        self.mama = MAMAIndicator()

    def next(self):
        print(self.mama.mama[0], self.mama.fama[0], self.mama.fama[-1], self.mama.mama[-1])
        # Example: Buy if MAMA crosses above FAMA
        if self.mama.mama[0] > self.mama.fama[0] and self.mama.mama[-1] <= self.mama.fama[-1]:
            self.buy()
            print('Buy')
