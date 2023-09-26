import backtrader as bt
import math
from strategies.src.indicators.talib_sma import TALibSMA


class CryptoIndicator(bt.Indicator):
    lines = ('score',)
    params = (
        ('a', 1.5),  # constant for increasing speed
        ('b', 3),  # constant for decreasing speed
        ('c', 0.1),  # constant to scale the stock price or its difference
        ('period', 5),
    )

    def __init__(self):
        self.addminperiod(10)
        # You may need to ensure that self.data has enough bars before calculating KAMA
        self.kama = TALibSMA(period=self.p.period)

    def next(self):
        P = self.kama[0] - self.kama[-1]  # using KAMA as the stock price
        score_increasing = 2 / (1 + math.exp(-self.params.a * (self.params.c * P - 1))) - 1
        score_decreasing = 2 / (1 + math.exp(self.params.b * (self.params.c * P - 1)))
        self.lines.score[0] = score_increasing - score_decreasing


class CryptoStrategy(bt.Strategy):
    def __init__(self):
        self.custom_ind = CryptoIndicator()

    def next(self):
        # Access the indicator value for the current bar and perform your logic
        score = self.custom_ind.score[0]
        print(f'{self.data.datetime.date(0)} - Score: {score}')
