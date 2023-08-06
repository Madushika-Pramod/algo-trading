import backtrader as bt
from app.src.constants import average_volume, min_price


class SmaCrossStrategy(bt.Strategy):
    # Configurable parameters for the strategy
    params = dict(
        fast_ma_period=3,  # Period for the fast moving average
        slow_ma_period=15,  # Period for the slow moving average
        high_low_period=20,  # Period for tracking highest and lowest prices
        high_low_tolerance=0.15,  # Tolerance for approximating high or low prices
        profit_threshold=2  # Threshold to decide when to sell based on profit

    )

    def __init__(self):
        # Initial attributes to track trades, profits, and orders

        self.order_active = None
        self.trading_count = 0
        self.total_return_on_investment = None
        self.commission_on_last_purchase = None
        self.price_of_last_sale = None
        self.price_of_last_purchase = None
        self.starting_balance = self.broker.get_cash()  # Retrieve starting balance
        self.cumulative_profit = 0.0
        self.ready_to_buy = False
        self.ready_to_sell = False
        # self.price_at_last_buy = None
        # self.price_at_last_sell = None

        # Indicators for strategy
        fast_moving_avg = bt.ind.MovingAverageSimple(period=self.p.fast_ma_period)
        slow_moving_avg = bt.ind.MovingAverageSimple(period=self.p.slow_ma_period)
        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)
        self.moving_avg_crossover_indicator.plotinfo.plot = False
        self.recorded_highest_price = bt.indicators.Highest(self.data.close, period=self.p.high_low_period)
        self.recorded_lowest_price = bt.indicators.Lowest(self.data.close, period=self.p.high_low_period)

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """Handle the events of executed orders."""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.price_of_last_purchase = order.executed.price
                self.commission_on_last_purchase = order.executed.comm
                self.log(f"Commission on Buy: {order.executed.comm}")
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.price_of_last_sale = order.executed.price
                # Calculate cumulative profit/loss after selling
                self.cumulative_profit += ((self.price_of_last_sale - self.price_of_last_purchase) * abs(
                    order.executed.size)) - self.commission_on_last_purchase
                self.trading_count += 1
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def stop(self):
        # Calculate the ROI based on the net profit and starting balance
        self.total_return_on_investment = self.cumulative_profit / self.starting_balance

    # Main strategy logic
    def next(self):
        # 1. If the price drops more than 'profit_threshold' from the bought price,
        # sell immediately and stop trading
        if self.price_of_last_purchase is not None and self.p.profit_threshold < self.price_of_last_purchase - self.data.close[0]:
            self.sell()
            self.stop()
            return

        # 2. If there's no existing buy order, consider buying
        # notice:we can't use `if not self.order_active:`
        if self.order_active is False:

            # 3. If there was a prior sell price, only buy if the difference
            # between the prior sell price and current price exceeds 'profit_threshold'
            if self.price_of_last_sale is not None and self.p.profit_threshold > self.price_of_last_sale - self.data.close[0]:
                return

            # 4. Enter into buy state if the close price is near the lowest price
            if self.data.close[0] - self.recorded_lowest_price[0] < self.p.high_low_tolerance:
                self.ready_to_buy = True
            else:
                self.ready_to_buy = False

            # 5. If in buy state, and volume is sufficient, and there's a positive crossover, then buy
            if self.ready_to_buy and self.data.volume[0] > average_volume and self.moving_avg_crossover_indicator > 0:
                self.buy()
                # TrailingStopOrderRequest
                self.ready_to_buy = False
                self.order_active = True
                # self.price_of_last_purchase = self.data.close[0]

        # 6. If a buy order has been executed, consider selling
        elif self.order_active:

            # 7. If the gain from the bought price exceeds 'profit_threshold', continue without selling
            if self.p.profit_threshold > self.data.close[0] - self.price_of_last_purchase:
                return

            # 8. Enter into sell state if the close price is near the highest price
            if self.recorded_highest_price[0] - self.data.close[0] < self.p.high_low_tolerance:
                self.ready_to_sell = True
            else:
                self.ready_to_sell = False

            # 9. If in sell state, and volume is sufficient, and there's a negative crossover, then sell
            if self.ready_to_sell and self.data.volume[0] > average_volume and self.moving_avg_crossover_indicator < 0:
                self.sell()
                self.ready_to_sell = False
                self.order_active = False
                # self.price_of_last_sale = self.data.close[0]

        # Initiate strategy: If the current close price is below 'min_price', make the initial buy
        elif self.order_active is None and self.data.close[0] <= min_price:
            self.buy()
            self.ready_to_buy = False
            self.order_active = True
            # self.price_of_last_purchase = self.data.close[0]
