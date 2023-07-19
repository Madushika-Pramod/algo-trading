import backtrader as bt


class SmaCrossStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=None,  # 50 period for the fast moving average
        pslow=None  # 200 period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.MovingAverageSimple(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.MovingAverageSimple(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        self.order = None
        # self.sell_cont = 0
        # self.buy_count = 0

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        # print(f'{dt.isoformat()}, {txt}')  # Print date and log message

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # print("strategy executed")
        #
        # print(self.data.close[0])
        if self.crossover > 0:  # if fast crosses slow to the upside

            # self.close() #todo with uncommenting order wll add twice
            # print(self.position)
            self.order = self.buy()  # enter long
            # self.buy_count += 1
            # print("Buy {} shares".format(self.data.close[0]))
            # print(self.position)


        elif self.crossover < 0:  # in the market & cross to the downside

            # self.close()  # close long position #todo with uncommenting order wll add twice
            # print(self.position)
            self.sell()
            # self.sell_cont += 1
            # print("Sale {} shares".format(self.data.close[0]))
            # print(self.position)

    # def stop(self):

        # print("Sell count : {}\nBuy count : {}".format(self.sell_cont, self.buy_count))
