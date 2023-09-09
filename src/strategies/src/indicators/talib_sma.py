from backtrader import Indicator
from backtrader.talib import KAMA


class TALibSMA(Indicator):
    lines = ('kama',)
    params = (('period', 15),)

    def __init__(self):
        self.lines.kama = KAMA(self.data.close, timeperiod=self.p.period)
