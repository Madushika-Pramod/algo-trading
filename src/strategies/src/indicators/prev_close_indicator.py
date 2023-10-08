from backtrader import Indicator


class PrevCloseIndicator(Indicator):
    lines = ('prev_close',)
    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        prev_close=dict(ls='--', color='black', _plotskip='True'),
    )

    def __init__(self):
        self.addminperiod(2)

    def next(self):
        self.lines.prev_close[0] = self.data.close[-1]