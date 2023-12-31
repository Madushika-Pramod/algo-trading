import threading

import backtrader as bt

from app.src import constants
from broker.alpaca_trader import AlpacaTrader, get_trade_updates
from app.src.constants import median_volume, min_price  # todo add these as parameters
from app.src.voice_alert import voice_alert


class SmaCrossStrategy(bt.Strategy):
    # Configurable parameters for the strategy
    params = dict(
        fast_ma_period=3,  # Period for the fast moving average
        slow_ma_period=15,  # Period for the slow moving average
        high_low_period=20,  # Period for tracking highest and lowest prices
        high_low_tolerance=0.15,  # Tolerance for approximating high or low prices
        profit_threshold=2,  # Threshold to decide when to sell based on profit

    )

    def __init__(self):
        self.live_mode = False
        self.trader = None
        self.algorithm_performed_sell_order_id = None
        self.algorithm_performed_buy_order_id = None

        self.order_active = None
        self.trading_count = 0
        self.total_return_on_investment = None
        self.commission_on_last_purchase = None
        self.price_of_last_sale = 0
        self.price_of_last_purchase = 0
        self.starting_balance = self.broker.get_cash()
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

    def back_test(self):
        # 1. If the price drops more than 'profit_threshold' from the bought price,
        # sell immediately and stop trading
        # todo change profit * 10
        if self.price_of_last_purchase is not None and self.p.profit_threshold * 4 < self.price_of_last_purchase - \
                self.data.close[0]:
            self.price_of_last_sale = self.data.close[0]
            self.sell()
            self.stop()
            raise Exception("===xxx Trading Terminated xxx===")

        # 2. If there's no existing buy order, consider buying
        # notice:we can't use `if not self.order_active:`
        if self.order_active is False:

            # 3. If there was a prior sell price, only buy if the difference
            # between the prior sell price and current price exceeds 'profit_threshold'
            if self.price_of_last_sale is not None and self.p.profit_threshold > self.price_of_last_sale - \
                    self.data.close[0]:
                return

            # 4. Enter into buy state if the close price is near the lowest price
            if self.data.close[0] - self.recorded_lowest_price[0] < self.p.high_low_tolerance:
                self.ready_to_buy = True
            else:
                self.ready_to_buy = False

            # 5. If in buy state, and volume is sufficient, and there's a positive crossover, then buy
            if self.ready_to_buy and self.data.volume[
                0] > median_volume and self.moving_avg_crossover_indicator > 0:
                self.buy()
                self.ready_to_buy = False
                self.order_active = True
                self.price_of_last_purchase = self.data.close[0]
        # 6. If a buy order has been executed, consider selling
        elif self.order_active:

            # 7. If the gain from the bought price exceeds 'profit_threshold', continue without selling
            if self.p.profit_threshold / 2 > self.data.close[0] - self.price_of_last_purchase:
                return

            # 8. Enter into sell state if the close price is near the highest price
            if self.recorded_highest_price[0] - self.data.close[0] < self.p.high_low_tolerance:
                self.ready_to_sell = True
            else:
                self.ready_to_sell = False

            # 9. If in sell state, and volume is sufficient, and there's a negative crossover, then sell
            if self.ready_to_sell and self.data.volume[
                0] > median_volume and self.moving_avg_crossover_indicator < 0:
                self.price_of_last_sale = self.data.close[0]
                self.sell()
                self.ready_to_sell = False
                self.order_active = False


        # Initiate strategy: If the current close price is below 'min_price', make the initial buy
        elif self.order_active is None and self.data.close[0] <= min_price:
            self.price_of_last_purchase = self.data.close[0]
            self.buy()
            self.ready_to_buy = False
            self.order_active = True

    def live(self):
        print(f'live-{self.data.close[0]}--time-{self.data.datetime[0]}')
        # 11. buy only if when order has been executed on alpaca
        if constants.accepted_order is not None and constants.accepted_order['id'] == str(
                self.algorithm_performed_buy_order_id):
            print("buy executed")
            self.buy()
            self.ready_to_buy = False
            self.order_active = True
            self.price_of_last_purchase = float(constants.accepted_order['stop_price'])
            constants.accepted_order = None
        # 12. sell only if when order has been executed on alpaca
        elif constants.accepted_order is not None and constants.accepted_order['id'] == str(
                self.algorithm_performed_sell_order_id):
            print("sell executed")
            self.price_of_last_sale = float(constants.accepted_order['stop_price'])
            self.sell()
            self.ready_to_sell = False
            self.order_active = False
            constants.accepted_order = None


        # cancel pending order if not executed
        elif constants.pending_order is not None and float(constants.pending_order['hwm']) - self.data.close[
            0] > self.p.profit_threshold / 4 \
                and not self.order_active:

            self.trading_client.cancel_order_by_id(constants.pending_order['id'])
            voice_alert(f"say the buy order made at a price {constants.pending_order['hwm']} has been canceled", 2)

        elif constants.pending_order is not None and self.data.close[0] - float(
                constants.pending_order['hwm']) > self.p.profit_threshold / 4 \
                and self.order_active:

            self.trading_client.cancel_order_by_id(constants.pending_order['id'])
            voice_alert(f"say the sell order made at a price {float(constants.pending_order['hwm'])} has been canceled",
                        2)

        # 1. If the price drops more than 'profit_threshold' from the bought price,
        # sell immediately and stop trading
        if self.price_of_last_purchase is not None \
                and self.p.profit_threshold * 4 < self.price_of_last_purchase - self.data.close[0]:
            r = self.traderself.trading_client.close_all_positions(cancel_orders=True)
            print(r)
            voice_alert("say Warning! The price has dropped significantly low. Trading has been stopped.", 5)
            print("immediately sold")
            self.stop()
            raise Exception("===xxx Trading Terminated xxx===")
        # ========== al_data = self.data_queue.get_nowait() ==========#
        # =========== if al_data:

        # 2. If there's no existing buy order, consider buying
        # notice:we can't use `if not self.order_active:`
        if self.order_active is False:

            # 3. If there was a prior sell price, only buy if the difference
            # between the prior sell price and current price exceeds 'profit_threshold'
            if self.price_of_last_sale is not None and self.p.profit_threshold > self.price_of_last_sale - \
                    self.data.close[0]:
                return

            # 4. Enter into buy state if the close price is near the lowest price
            if self.data.close[0] - self.recorded_lowest_price[0] < self.p.high_low_tolerance:
                self.ready_to_buy = True
            else:
                self.ready_to_buy = False

            # 5. If in buy state, and volume is sufficient, and there's a positive crossover, then buy
            if self.ready_to_buy and self.data.volume[
                0] > constants.median_volume and self.moving_avg_crossover_indicator > 0:
                self.algorithm_performed_buy_order_id = self.trader.buy(self.data.close[0])

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
            if self.ready_to_sell and self.data.volume[
                0] > constants.median_volume and self.moving_avg_crossover_indicator < 0:
                self.algorithm_performed_sell_order_id = self.trader.sell(self.data.close[0])

        # this is just for buy test purpose only will be deleted in future
        elif self.order_active is None and self.data.close[0] <= constants.min_price and self.data.close[-1] == 0:
            self.algorithm_performed_buy_order_id = self.trader.buy(self.data.close[0])
            print(f'initial buy order Id={str(self.algorithm_performed_buy_order_id)}')

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """Handle the events of executed orders."""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.commission_on_last_purchase = order.executed.comm
                self.log(f"Commission on Buy: {order.executed.comm}")
                # self.log('BUY EXECUTED, %.2f' % order.executed.price)  # executing.price for a buy is next bar's open price
                self.log('BUY EXECUTED, %.2f' % self.price_of_last_purchase)
            elif order.issell():

                # Calculate cumulative profit/loss after selling
                self.cumulative_profit += (self.price_of_last_sale - self.price_of_last_purchase) * abs(
                    order.executed.size) - self.commission_on_last_purchase

                self.trading_count += 1
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
                print(f"total profit on trades:{self.cumulative_profit}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def stop(self):
        # Calculate the ROI based on the net profit and starting balance
        self.total_return_on_investment = self.cumulative_profit / self.starting_balance
        if self.live_mode:
            self.trader.trading_client.cancel_orders()
            print("pending orders canceled")

    # Main strategy logic
    def next(self):
        # if self.live_mode:
        #     try:
        #         self.live()
        #     except KeyboardInterrupt:
        #         print("KeyboardInterrupt received. shutting down trader...")
        #         self.trader.trading_client.cancel_orders()
        #         # todo add stop order for pre-market period
        #         # doesn't reach todo
        #
        # else:
        # if self.data.close[0] == 0:
        #     self.total_return_on_investment = self.cumulative_profit / self.starting_balance
        #
        #     # voice_alert(
        #     #     "say  the back testing has been completed. " +
        #     #     f"the return on investment is {round(self.total_return_on_investment * 100, 1)}% " +
        #     #     f"and the trading count is {self.trading_count}", 1)
        #
        #     print(f"Roi= {round(self.total_return_on_investment * 100, 3)}%\nTrading Count= {self.trading_count}")
        #     self.live_mode = True
        #     self.trader = AlpacaTrader()
        #     self.starting_balance = float(self.trader.cash)
        #     self.trading_count = 0
        #     self.total_return_on_investment = 0
        #     positions = self.trader.trading_client.get_all_positions()
        #     if len(positions):  # todo test
        #         # force to sell if any sell orders left in Alpaca
        #         self.ready_to_buy = False
        #         self.order_active = True
        #         self.price_of_last_purchase = positions[0].avg_entry_price
        #     else:
        #         # force to buy if no any sell orders left in Alpaca
        #         self.ready_to_sell = False
        #         self.order_active = False
        #         self.order_active = None  # todo remove
        #
        #     thread = threading.Thread(target=get_trade_updates)  # start trade updates
        #     thread.start()
        #
        #     return
        if self.cerebro.params.live:

            if self.live_mode:
                try:
                    self.live()
                except KeyboardInterrupt:
                    print("KeyboardInterrupt received. shutting down trader...")
                    self.trader.trading_client.cancel_orders()
                    # todo add stop order for pre-market period
                    # doesn't reach todo

            elif self.data.close[0] == 0:

                self.live_mode = True
                self.trader = AlpacaTrader()
                self.starting_balance = float(self.trader.cash)
                self.trading_count = 0
                self.total_return_on_investment = 0
                constants.median_volume = 500
                positions = self.trader.trading_client.get_all_positions()
                print(len(positions))
                if len(positions):  # todo test
                    # this is a fake sell state if any sell orders left in Alpaca
                    self.ready_to_buy = False
                    self.order_active = True
                    if len(positions) == 2:  # if market order and stop order exists
                        self.price_of_last_purchase = positions[0].avg_entry_price if positions[0].qty > positions[
                            1].qty else positions[1].avg_entry_price
                    else:  # if 1 order exists
                        self.price_of_last_purchase = positions[0].avg_entry_price
                else:
                    # this is a fake buy state if no any sell orders left in Alpaca
                    self.ready_to_sell = False
                    self.order_active = False
                    # initially, make algorithm to ignore profit_threshold
                    self.price_of_last_sale = self.data.close[0] + self.p.profit_threshold + 0.01
                print('316')
                thread = threading.Thread(target=get_trade_updates)  # start trade updates
                thread.start()

        else:
            self.back_test()
