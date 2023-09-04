import logging

import backtrader as bt

from app.src import constants
# from broker import AlpacaTrader, get_trade_updates
from app.src.constants import median_volume  # todo add these as parameters
from app.src.notify import news
from broker import AlpacaTrader


class TALibSMA(bt.Indicator):
    lines = ('kama',)
    params = (('period', 15),)

    def __init__(self):
        self.lines.kama = bt.talib.KAMA(self.data.close, timeperiod=self.p.period)


class SmaCrossstrategyV2(bt.Strategy):
    # Configurable parameters for the strategy
    params = dict(
        fast_ma_period=3,  # Period for the fast moving average
        slow_ma_period=15,  # Period for the slow moving average
        high_low_period=20,  # Period for tracking highest and lowest prices
        high_low_tolerance=0.15,  # Tolerance for approximating high or low prices
        buy_profit_threshold=2,  # Threshold to decide when to sell based on profit
        sell_profit_threshold=2,

    )

    def __init__(self):

        self.live_mode = False
        self.trader = None
        self.algorithm_performed_sell_order_id = None
        self.algorithm_performed_buy_order_id = None

        self.trade_active = None  # None
        self.trading_count = 0
        self.total_return_on_investment = 0
        self.commission_on_last_purchase = 0
        self.price_of_last_sale = 0
        self.price_of_last_purchase = 0
        self.starting_balance = self.broker.get_cash()
        self.cumulative_profit = 0.0
        self.ready_to_buy = False
        self.ready_to_sell = False

        # Indicators for strategy
        fast_moving_avg = TALibSMA(self.data, period=self.p.fast_ma_period)
        slow_moving_avg = TALibSMA(self.data, period=self.p.slow_ma_period)

        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)
        self.moving_avg_crossover_indicator.plotinfo.plot = False
        self.recorded_highest_price = bt.indicators.Highest(self.data.close, period=self.p.high_low_period)
        self.recorded_lowest_price = bt.indicators.Lowest(self.data.close, period=self.p.high_low_period)

        self.trader = AlpacaTrader()
        self.live_mode = True
        self.starting_balance = float(self.trader.cash)  # to be commented out

    def _roi(self):
        return self.cumulative_profit / self.starting_balance

    def _is_initial_buy_condition(self):
        return self.trade_active is None and self.data.close[0] <= constants.min_price

    def _buy_orders_ready_on_alpaca(self):
        return constants.accepted_order is not None and constants.accepted_order['id'] == str(
            self.algorithm_performed_buy_order_id)

    def _execute_buy_orders(self):
        logging.info("177 -buy executed")
        self.buy()
        self._reset_buy_state()
        self.price_of_last_purchase = float(constants.accepted_order['stop_price'])
        constants.accepted_order = None

    def _sell_orders_ready_on_alpaca(self):
        return constants.accepted_order is not None and constants.accepted_order['id'] == str(
            self.algorithm_performed_sell_order_id)

    def _execute_sell_orders(self):
        logging.info("192 -sell executed")
        self.price_of_last_sale = float(constants.accepted_order['stop_price'])
        self.sell()
        self._reset_sell_state()
        constants.accepted_order = None

    def _need_to_cancel_buy_order(self):
        return constants.pending_order is not None and float(constants.pending_order['hwm']) - self.data.close[
            0] > self.p.buy_profit_threshold / 4 and not self.trade_active

    def _cancel_buy_order(self):
        self._cancel_order(constants.pending_order['id'])
        constants.pending_order = None
        logging.info(f"205 -buy order placed at the price {constants.pending_order['hwm']} has been canceled")

    def _need_to_cancel_sell_order(self):
        return constants.pending_order is not None and self.data.close[0] - float(
            constants.pending_order['hwm']) > self.p.sell_profit_threshold / 4 and self.trade_active

    def _cancel_sell_order(self):
        self._cancel_order(constants.pending_order['id'])
        logging.info(f"213 -sell order placed at the price {constants.pending_order['hwm']} has been canceled")

    def _significant_stock_price_drop(self):
        return self.price_of_last_purchase is not None and constants.loss_value < self.price_of_last_purchase - \
            self.data.close[0]

    def _halt_trading_and_alert(self):
        """
                If the price drops more than 'profit_threshold' from the bought price,
                sell immediately and stop trading.
                TODO: introduce here a sps mopeed parameter and implement for both buy and sell.
                """
        _ = self.trader.trading_client.close_all_positions(cancel_orders=True)
        # logging.info(f'119 -close_all_positions:{_}')
        logging.critical("immediately sold")
        self.stop()
        raise Exception(f"Trading Terminated and immediately sold due to significant drop of price,\nbuy_profit_threshold * 4 < price_of_last_purchase - current price = {self.p.buy_profit_threshold} x 4 < {self.price_of_last_purchase} - {self.data.close[0]}  ")

    def _conditions_met_for_buy(self):
        return self.trade_active is False  # todo chnage this

    def _start_buy_process(self):
        """If there's no existing buy order, consider buying"""
        if self._is_prior_sell_price_close_to_current():
            logging.info('130 -inactive trade returned')
            return

        if self._is_price_near_lowest():
            self.ready_to_buy = True
            logging.info('239 -ready_to_buy = True')
        else:
            self.ready_to_buy = False
            logging.info('241 -ready_to_buy = False')

        if self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():
            self.algorithm_performed_buy_order_id = self.trader.buy(self.data.close[0])
            logging.debug(f'242 -buy id: {self.algorithm_performed_buy_order_id}')
            logging.debug(
                f'trade_active:{self.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.p.buy_profit_threshold} > {self.price_of_last_sale} - {self.data.close[0]}<==>close price - recorded_lowest_price < high_low_tolerance={self.data.close[0]} - {self.recorded_lowest_price[0]} < {self.p.high_low_tolerance}<==>ready_to_buy: {self.ready_to_buy},volume > median_volume ={self.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator > 0 = {self.moving_avg_crossover_indicator}')
        if not self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():

            self.buy()
            self._reset_buy_state()
            self.price_of_last_purchase = self.data.close[0]

    def _conditions_met_for_sell(self):
        """If a buy order has been executed, consider selling"""
        return self.trade_active

    def _start_sell_process(self):
        if not self._profit():
            # logging.info('156 -active trade returned')
            return

        if self._is_price_near_highest():
            self.ready_to_sell = True
            # logging.info('255 -ready_to_sell = True')
        else:
            self.ready_to_sell = False
            # logging.info('258 -ready_to_sell = False')

        if self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
            self.algorithm_performed_sell_order_id = self.trader.sell(self.data.close[0]) # this step executing
            logging.debug(f'263 -sell id: {self.algorithm_performed_sell_order_id}')
            logging.debug(
                f'trade_active:{self.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.p.sell_profit_threshold} > {self.data.close[0]} - {self.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.recorded_highest_price[0]} - {self.data.close[0]} < {self.p.high_low_tolerance}<==>ready_to_sell: {self.ready_to_sell},volume > median_volume ={self.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator < 0 = {self.moving_avg_crossover_indicator}')

        elif not self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
            self.price_of_last_sale = self.data.close[0]
            self.sell()
            self._reset_sell_state()

    def _initial_buy(self):
        """Initiate strategy: If the current close price is below 'min_price', make the initial buy"""

        self.price_of_last_purchase = self.data.close[0]
        self.buy()
        self._reset_buy_state()

    def _reset_buy_state(self):
        self.ready_to_buy = False
        self.trade_active = True

    def _reset_sell_state(self):
        self.ready_to_sell = False
        self.trade_active = False

    def _cancel_order(self, order_id):
        self.trader.trading_client.cancel_order_by_id(order_id)

    def _is_prior_sell_price_close_to_current(self):
        """If there was a prior sell price, only buy if the difference between the prior sell price and current price 
        exceeds 'profit_threshold'"""
        return self.price_of_last_sale is not None and self.p.buy_profit_threshold > self.price_of_last_sale - \
            self.data.close[0]

    def _is_price_near_lowest(self):
        """Enter into buy state if the close price is near the lowest price"""
        return self.data.close[0] - self.recorded_lowest_price[0] < self.p.high_low_tolerance

    def _is_ready_to_buy_based_on_volume_and_crossover(self):
        """If in buy state, and volume is sufficient, and there's a positive crossover, then buy"""
        return self.ready_to_buy and self.data.volume[
            0] > constants.median_volume and self.moving_avg_crossover_indicator > 0

    def _profit(self):
        """If the gain from the bought price exceeds 'profit_threshold', continue without selling"""
        return self.p.sell_profit_threshold <= self.data.close[0] - self.price_of_last_purchase

    def _is_price_near_highest(self):
        """Enter into sell state if the close price is near the highest price"""
        return self.recorded_highest_price[0] - self.data.close[0] < self.p.high_low_tolerance

    def _is_ready_to_sell_based_on_volume_and_crossover(self):
        """If in sell state, and volume is sufficient, and there's a negative crossover, then sell"""
        return self.ready_to_sell and self.data.volume[
            0] > constants.median_volume and self.moving_avg_crossover_indicator < 0

    def _start_trade(self):
        # Initiate a buy if conditions are met
        if self._conditions_met_for_buy():
            self._start_buy_process()

        # Initiate a sell if conditions are met
        elif self._conditions_met_for_sell():
            self._start_sell_process()

        # it doesn't execute this step if live trading
        elif self._is_initial_buy_condition():
            # print('235')
            self.algorithm_performed_buy_order_id = self.trader.buy(self.data.close[0])
            logging.debug(f'236 -buy id: {self.algorithm_performed_buy_order_id}')

            # self._initial_buy()

    def _check_alpaca_status(self):
        # Check and execute buy orders on alpaca
        if self._buy_orders_ready_on_alpaca():
            self._execute_buy_orders()

        # Check and execute sell orders on alpaca
        elif self._sell_orders_ready_on_alpaca():
            self._execute_sell_orders()

        # Cancel any pending buy order
        if self._need_to_cancel_buy_order():
            self._cancel_buy_order()
            news(f"buy order placed at the price {constants.pending_order['hwm']} has been canceled")

        # Cancel any pending sell order
        elif self._need_to_cancel_sell_order():
            self._cancel_sell_order()
            news(f"the sell order placed at the price {(constants.pending_order['hwm'])} has been canceled")

        # Halt trading if there's a significant drop in stock prices
        if self._significant_stock_price_drop():
            self._halt_trading_and_alert()
            news("⚠️ The price has dropped significantly low. Trading has been stopped.")

    def back_test(self):
        self._start_trade()

    def live(self):

        print(f'live-{self.data.close[0]}')

        # todo turn this to an event
        self._check_alpaca_status()

        self._start_trade()

    def log(self, txt, dt=None):
        """ Logging function for the strategy """
        dt = dt or self.datas[0].datetime.date(0)
        logging.info(f'{dt.isoformat()}, {txt}')

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
                # print(f"total profit on trades:{self.cumulative_profit}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def stop(self):
        # Calculate the ROI based on the net profit and starting balance
        self.total_return_on_investment = self._roi()
        # print(f'Last sale : {self.price_of_last_sale}')
        if self.live_mode:
            self.trader.trading_client.cancel_orders()
            # logging.info("266 -pending orders canceled")

    # Main strategy logic
    def next(self):
        self.live()

        # if self.cerebro.params.live:
        #
        #     if self.live_mode:
        #         try:
        #             self.live()
        #         except KeyboardInterrupt:
        #             print("KeyboardInterrupt received. shutting down trader...")
        #             self.trader.trading_client.cancel_orders()
        #             logging.info("318 -KeyboardInterrupt")
        #             # todo add stop order for pre-market period
        #             # doesn't reach todo
        #
        #     elif self.data.close[0] == 0:
        #
        #         logging.info(f'Last sale : {self.price_of_last_sale}')
        #         logging.info(
        #             f"Number of Trades: {self.trading_count}\nReturn on investment: {round(self._roi() * 100, 3)}%")
        #
        #         self.live_mode = True
        #         self.trading_count = 0
        #         self.total_return_on_investment = 0
        #
        #         self.trader = AlpacaTrader()
        #         self.starting_balance = float(self.trader.cash)
        #
        #         constants.median_volume = 99
        #
        #         positions = self.trader.trading_client.get_all_positions()
        #         logging.info(f'Number of Positions: {len(positions)}')
        #         if len(positions):  # todo test
        #             # this is a fake buy state if any buy orders left in Alpaca,
        #             # make algorithm to sell in the future
        #             self.ready_to_buy = False
        #             self.trade_active = True
        #
        #             if len(positions) == 2:  # if market order and stop order exists
        #                 self.price_of_last_purchase = float(positions[0].avg_entry_price) if positions[0].qty > \
        #                                                                                      positions[
        #                                                                                          1].qty else positions[
        #                     1].avg_entry_price
        #             else:  # if 1 order exists
        #                 self.price_of_last_purchase = float(positions[0].avg_entry_price)
        #             logging.info(f'Last buy : {self.price_of_last_purchase}')
        #         else:
        #             # this is a fake sell state if no any sell orders left in Alpaca
        #             # make algorithm to buy in the future
        #             self.ready_to_sell = False
        #             self.trade_active = False
        #             # initially, make algorithm to ignore profit_threshold
        #             self.price_of_last_sale = constants.last_sale_price or self.price_of_last_sale  # todo optimize this-> back test should find out this value
        #         thread = threading.Thread(target=get_trade_updates)  # start trade updates
        #         thread.start()
        #     else:
        #         self.back_test()
        #
        # else:
        #     self.back_test()
