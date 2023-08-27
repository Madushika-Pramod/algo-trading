import backtrader as bt


class DemoStrategy(bt.Strategy):
    def __init__(self):
        self.trading_count = 100
        self.total_return_on_investment = 1


    def next(self):
        print("bt.Strategy executed")
        print(self.data.close[0])
        # if self.order is None:  # if fast crosses slow to the upside
        #     self.close()
        #     self.order = self.buy()
        # else:
        #     self.close()  # close long position
        #     self.sell()
