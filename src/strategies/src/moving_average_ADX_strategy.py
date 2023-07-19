import backtrader as bt


class MovingAverageADXStrategy(bt.Strategy):
    params = dict(
        fast=5,
        slow=20,
        adx_period=14,
        adx_level=20
        # ('stop_loss_percentage', 0.02),  # 2% stop loss
        # ('take_profit_percentage', 0.04),  # 4% take profit
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        sma1 = bt.ind.MovingAverageSimple(period=self.p.fast)  # fast moving average
        sma2 = bt.ind.MovingAverageSimple(period=self.p.slow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)
        self.adx = bt.ind.AverageDirectionalMovementIndex()
        self.position_size = False

        self.order = None
        # self.stop_loss_order = None
        # self.take_profit_order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        # Cancel any existing stop loss and take profit orders
        # if self.stop_loss_order:
        #     self.cancel(self.stop_loss_order)
        # if self.take_profit_order:
        #     self.cancel(self.take_profit_order)

        if not self.position_size and self.crossover > 0 and self.data[0] > self.params.adx_level:
            self.order = self.buy()
            self.position_size = True
            # stop_price = self.data.close[0] * (1 - self.params.stop_loss_percentage)
            # take_profit_price = self.data.close[0] * (1 + self.params.take_profit_percentage)
            # self.stop_loss_order = self.sell(
            #     exectype=bt.Order.Stop,
            #     price=stop_price,
            #     parent=self.order
            # )
            # self.take_profit_order = self.sell(
            #     exectype=bt.Order.Limit,
            #     price=take_profit_price,
            #     parent=self.order
            # )
        elif self.position_size and self.crossover < 0 and self.adx[0] > self.params.adx_level:
            # self.order = self.sell()
            self.sell()
            self.position_size = False
            # stop_price = self.data.close[0] * (1 + self.params.stop_loss_percentage)
            # take_profit_price = self.data.close[0] * (1 - self.params.take_profit_percentage)
            # self.stop_loss_order = self.buy(
            #     exectype=bt.Order.Stop,
            #     price=stop_price,
            #     parent=self.order
            # )
            # self.take_profit_order = self.buy(
            #     exectype=bt.Order.Limit,
            #     price=take_profit_price,
            #     parent=self.order
            # )

    def stop(self):
        self.log('Final Portfolio Value: %.2f' % self.broker.getvalue())
