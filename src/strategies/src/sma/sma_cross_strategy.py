import logging
import threading

import backtrader as bt

from app.src import constants
from app.src.constants import median_volume  # todo add these as parameters
from app.src.notify import news
from broker import AlpacaTrader, get_trade_updates


class TALibSMA(bt.Indicator):
    lines = ('kama',)
    params = (('period', 15),)

    def __init__(self):
        self.lines.kama = bt.talib.KAMA(self.data.close, timeperiod=self.p.period)


class SmaCrossStrategyState:

    def __init__(self, buying_power):
        self.starting_balance = buying_power  # to be commented out
        self.current_balance = buying_power

        self.order_quantity = 0
        self.algorithm_performed_sell_order_id = None
        self.algorithm_performed_buy_order_id = None
        self.trade_active = None  # None
        self.trading_count = -1
        self.total_return_on_investment = -1
        self.commission_on_last_purchase = -1
        self.price_of_last_sale = -1
        self.price_of_last_purchase = -1
        self.cumulative_profit = -1.0
        self.ready_to_buy = False
        self.ready_to_sell = False

        self.trading_view_data = dict(volume=-1000, last_price=-1000, lp_time=-1000, cumulative_change=-1000,
                                      cc_percentage=-1000,
                                      extended_hours_price=-1000, ehp_percentage=-1000, close=-1000, open=-1000,
                                      high=-1000,
                                      low=-1000)
        self.pending_order = None
        self.accepted_order = None
        self.market_buy_order = False


class SmaCrossStrategyIndicators:

    def __init__(self, params, data):
        fast_moving_avg = TALibSMA(data, period=params.fast_ma_period)
        slow_moving_avg = TALibSMA(data, period=params.slow_ma_period)

        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)
        self.recorded_highest_price = bt.indicators.Highest(data.close, period=params.high_low_period)
        self.recorded_lowest_price = bt.indicators.Lowest(data.close, period=params.high_low_period)
        self.data = data
        self.params = params


class SmaCrossStrategy:
    def __init__(self, indicators: SmaCrossStrategyIndicators,state, trader=None):
        self.trader = trader
        self.state = state
        self.indicators = indicators

    def get_roi(self):
        return self.state.cumulative_profit / self.state.starting_balance

    def initial_buy_condition(self):
        return self.state.trade_active is None and self.indicators.data.close[0] <= constants.min_price

    def _buy_orders_ready_on_alpaca(self):
        return self.state.accepted_order is not None and self.state.accepted_order['id'] == str(
            self.state.algorithm_performed_buy_order_id)

    def _execute_buy_orders(self):
        logging.info("177 -buy executed")
        buy_price = float(self.state.accepted_order['stop_price'])
        self._reset_buy_state()
        self.state.price_of_last_purchase = buy_price
        self.state.accepted_order = None
        # current_balance = (previous sell -> order_quantity) * price_of_last_sale
        # order_quantity = current_balance /price
        self.state.order_quantity = int(
            self.state.order_quantity * self.state.price_of_last_sale / self.indicators.data.close[0])
        self.notify_order(True)

    def _sell_orders_ready_on_alpaca(self):
        return self.state.accepted_order is not None and self.state.accepted_order['id'] == str(
            self.state.algorithm_performed_sell_order_id)

    def _execute_sell_orders(self):
        logging.info("192 -sell executed")
        self.state.price_of_last_sale = float(self.state.accepted_order['stop_price'])
        self._reset_sell_state()
        self.state.accepted_order = None
        self.notify_order(False)

    def _need_to_cancel_buy_order(self):
        return not self.state.trade_active and self.state.pending_order is not None and float(
            self.state.pending_order['hwm']) - self.indicators.data.close[
            0] > self.indicators.params.buy_profit_threshold / 4

    def _cancel_buy_order(self):
        self._cancel_order(self.state.pending_order['id'])
        logging.info(f"205 -buy order placed at the price {self.state.pending_order['hwm']} has been canceled")
        self.state.pending_order = None

    def _need_to_cancel_sell_order(self):
        return self.state.trade_active and self.state.pending_order is not None and self.indicators.data.close[
            0] - float(
            self.state.pending_order['hwm']) > self.indicators.params.sell_profit_threshold / 4

    def _cancel_sell_order(self):
        self._cancel_order(self.state.pending_order['id'])
        logging.info(f"213 -sell order placed at the price {self.state.pending_order['hwm']} has been canceled")

    def _significant_stock_price_drop(self):
        return self.state.price_of_last_purchase is not None and constants.loss_value < self.state.price_of_last_purchase - \
            self.indicators.data.close[0]

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
        raise Exception(
            f"Trading Terminated and immediately sold due to significant drop of price,\nbuy_profit_threshold * 4 < price_of_last_purchase - current price = {self.indicators.params.buy_profit_threshold} x 4 < {self.state.price_of_last_purchase} - {self.indicators.data.close[0]}  ")

    def _conditions_met_for_buy(self):
        return self.state.trade_active is False  # todo chnage this

    def _start_buy_process(self, buy):
        """If there's no existing buy order, consider buying"""
        if self._is_prior_sell_price_close_to_current():
            logging.info('130 -inactive trade returned')
            return

        if self._is_price_near_lowest():
            self.state.ready_to_buy = True
            # news("I'm ready to place a buy order")
            logging.info('239 -ready_to_buy = True')
        else:
            self.state.ready_to_buy = False
            logging.info('241 -ready_to_buy = False')

        if self._is_ready_to_buy_based_on_volume_and_crossover():
            buy()
        # if self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():
        #     news("I placed a buy order")
        #     self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.data.close[0])
        #     logging.debug(f'242 -buy id: {self.state.algorithm_performed_buy_order_id}')
        #     logging.debug(f'trade_active:{self.state.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.indicators.params.buy_profit_threshold} > {self.state.price_of_last_sale} - {self.indicators.data.close[0]}<==>close price - recorded_lowest_price < high_low_tolerance={self.indicators.data.close[0]} - {self.indicators.recorded_lowest_price[0]} < {self.indicators.params.high_low_tolerance}<==>ready_to_buy: {self.state.ready_to_buy},volume > median_volume ={self.state.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator > 0 = {self.indicators.moving_avg_crossover_indicator}')
        # if not self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():
        #     self.buy()
        #     self._reset_buy_state()
        #     self.state.price_of_last_purchase = self.indicators.data.close[0]

    def _conditions_met_for_sell(self):
        """If a buy order has been executed, consider selling"""
        return self.state.trade_active

    def _start_sell_process(self, sell):
        if not self._is_profit():
            # logging.info('156 -active trade returned')
            return

        if self._is_price_near_highest():
            self.state.ready_to_sell = True
            news("I'm ready to place a sell order")
            # logging.info('255 -ready_to_sell = True')
        else:
            self.state.ready_to_sell = False
            # logging.info('258 -ready_to_sell = False')

        if self._is_ready_to_sell_based_on_volume_and_crossover():
            sell()
        # if self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
        #     news("I placed a sell order")
        #     self.state.algorithm_performed_sell_order_id = self.trader.sell(self.indicators.data.close[0])  # this step executing
        #     logging.debug(f'263 -sell id: {self.state.algorithm_performed_sell_order_id}')
        #     logging.debug(
        #         f'trade_active:{self.state.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.indicators.params.sell_profit_threshold} > {self.indicators.data.close[0]} - {self.state.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.recorded_highest_price[0]} - {self.indicators.data.close[0]} < {self.indicators.params.high_low_tolerance}<==>ready_to_sell: {self.state.ready_to_sell},volume > median_volume ={self.state.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator < 0 = {self.indicators.moving_avg_crossover_indicator}')
        #
        # elif not self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
        #     self.state.price_of_last_sale = self.indicators.data.close[0]
        #     self.sell()
        #     self._reset_sell_state()

    def _initial_buy(self):
        """Initiate strategy: If the current close price is below 'min_price', make the initial buy"""

        self.state.price_of_last_purchase = self.indicators.data.close[0]
        self.state.order_quantity = int(self.state.starting_balance / self.indicators.data.close[0])
        self.notify_order(True)
        self._reset_buy_state()

    def _reset_buy_state(self):
        self.state.ready_to_buy = False
        self.state.trade_active = True

    def _reset_sell_state(self):
        self.state.ready_to_sell = False
        self.state.trade_active = False

    def _cancel_order(self, order_id):
        self.trader.trading_client.cancel_order_by_id(order_id)

    def _is_prior_sell_price_close_to_current(self):
        """If there was a prior sell price, only buy if the difference between the prior sell price and current price
        exceeds 'profit_threshold'"""
        return self.state.price_of_last_sale is not None and self.indicators.params.buy_profit_threshold > self.state.price_of_last_sale - \
            self.indicators.data.close[0]

    def _is_price_near_lowest(self):
        """Enter into buy state if the close price is near the lowest price"""
        return self.indicators.data.close[0] - self.indicators.recorded_lowest_price[
            0] < self.indicators.params.high_low_tolerance

    def _is_ready_to_buy_based_on_volume_and_crossover(self):
        """If in buy state, and volume is sufficient, and there's a positive crossover, then buy"""
        return self.state.ready_to_buy and self.indicators.data.volume[
            0] > constants.median_volume and self.indicators.moving_avg_crossover_indicator > 0

    def _is_profit(self):
        """If the gain from the bought price exceeds 'profit_threshold', continue without selling"""
        return self.indicators.params.sell_profit_threshold <= self.indicators.data.close[
            0] - self.state.price_of_last_purchase

    def _is_price_near_highest(self):
        """Enter into sell state if the close price is near the highest price"""
        return self.indicators.recorded_highest_price[0] - self.indicators.data.close[
            0] < self.indicators.params.high_low_tolerance

    def _is_ready_to_sell_based_on_volume_and_crossover(self):
        """If in sell state, and volume is sufficient, and there's a negative crossover, then sell"""
        return self.state.ready_to_sell and self.indicators.data.volume[
            0] > constants.median_volume and self.indicators.moving_avg_crossover_indicator < 0

    def _start_trade(self, buy, sell):
        # Initiate a buy if conditions are met
        if self._conditions_met_for_buy():
            self._start_buy_process(buy)

        # Initiate a sell if conditions are met
        elif self._conditions_met_for_sell():
            self._start_sell_process(sell)

        # it doesn't execute this step if live trading
        elif self.initial_buy_condition():
            # print('235')
            # self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.data.close[0])
            # logging.debug(f'236 -buy id: {self.state.algorithm_performed_buy_order_id}')

            self._initial_buy()

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
            news(f"buy order placed at the price {self.state.pending_order['hwm']} has been canceled")

        # Cancel any pending sell order
        elif self._need_to_cancel_sell_order():
            self._cancel_sell_order()
            news(f"the sell order placed at the price {(self.state.pending_order['hwm'])} has been canceled")

        # Halt trading if there's a significant drop in stock prices
        if self._significant_stock_price_drop():
            self._halt_trading_and_alert()
            news("⚠️ The price has dropped significantly low. Trading has been stopped.")


    def back_test(self):
        # print(f'date-{self.indicators.data.close[0]}')
        def buy():
            self._reset_buy_state()
            self.state.price_of_last_purchase = self.indicators.data.close[0]
            # current_balance = (previous sell -> order_quantity) * price_of_last_sale
            # order_quantity = current_balance /price
            self.state.order_quantity = int(
                self.state.order_quantity * self.state.price_of_last_sale / self.indicators.data.close[0])
            self.notify_order(True)

        def sell():
            self.state.price_of_last_sale = self.indicators.data.close[0]
            self._reset_sell_state()
            self.notify_order(False)

        self._start_trade(buy, sell)

        # todo should return last sell price

    def live(self):
        print(f'date-{self.indicators.data.close[0]}')
        constants.median_volume = 99
        positions = self.trader.trading_client.get_all_positions()
        logging.info(f'Number of Positions: {len(positions)}')
        if len(positions):  # todo test
            # this is a fake buy state if any buy orders left in Alpaca,
            # make algorithm to sell in the future
            self.state.ready_to_buy = False
            self.state.trade_active = True

            if len(positions) == 2:  # if market order and stop order exists
                self.state.price_of_last_purchase = float(positions[0].avg_entry_price) if positions[0].qty > \
                                                                                           positions[
                                                                                               1].qty else positions[
                    1].avg_entry_price
            else:  # if 1 order exists
                self.state.price_of_last_purchase = float(positions[0].avg_entry_price)
            logging.info(f'Last buy : {self.state.price_of_last_purchase}')
        else:
            # this is a fake sell state if no any sell orders left in Alpaca
            # make algorithm to buy in the future
            self.state.ready_to_sell = False
            self.state.trade_active = False
            # initially, make algorithm to ignore profit_threshold
            self.state.price_of_last_sale = constants.last_sale_price or self.state.price_of_last_sale  # todo optimize this-> back test should find out this value
        thread = threading.Thread(target=get_trade_updates)  # start trade updates
        thread.start()
        print(f'live-{self.indicators.data.close[0]}')

        # todo turn this to an event
        self._check_alpaca_status()

        def buy():
            news("I placed a buy order")
            self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.data.close[0])
            logging.debug(f'242 -buy id: {self.state.algorithm_performed_buy_order_id}')
            logging.debug(
                f'trade_active:{self.state.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.indicators.params.buy_profit_threshold} > {self.state.price_of_last_sale} - {self.indicators.data.close[0]}<==>close price - recorded_lowest_price < high_low_tolerance={self.indicators.data.close[0]} - {self.indicators.recorded_lowest_price[0]} < {self.indicators.params.high_low_tolerance}<==>ready_to_buy: {self.state.ready_to_buy},volume > median_volume ={self.indicators.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator > 0 = {self.indicators.moving_avg_crossover_indicator}')

        def sell():
            news("I placed a sell order")
            self.state.algorithm_performed_sell_order_id = self.trader.sell(
                self.indicators.data.close[0])  # this step executing
            logging.debug(f'263 -sell id: {self.state.algorithm_performed_sell_order_id}')
            logging.debug(
                f'trade_active:{self.state.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.indicators.params.sell_profit_threshold} > {self.indicators.data.close[0]} - {self.state.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.indicators.recorded_highest_price[0]} - {self.indicators.data.close[0]} < {self.indicators.params.high_low_tolerance}<==>ready_to_sell: {self.state.ready_to_sell},volume > median_volume ={self.indicators.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator < 0 = {self.indicators.moving_avg_crossover_indicator}')

        self._start_trade(buy, sell)

    # def next(self):
    #     # my logic
    #     # Check for buy/sell signals
    #     if self.indicators.moving_avg_crossover > 0:  # if short MA crosses above long MA
    #         # self.buy()
    #         print('buy')
    #     elif self.indicators.moving_avg_crossover < 0:  # if short MA crosses below long MA
    #         # self.sell()
    #         print('sell')

    def stop(self):

        # Calculate the ROI based on the net profit and starting balance
        self.state.total_return_on_investment = self.get_roi()
        # print(f'Last sale : {self.price_of_last_sale}')
        # if self.cerebro.params.live:
        #     self.trader.trading_client.cancel_orders()
        # logging.info("266 -pending orders canceled")

    def log(self, txt, dt=None):
        """ Logging function for the strategy """
        dt = dt or bt.num2date(self.indicators.data.datetime[0])
        logging.info(f'{dt.isoformat()}, {txt}')

    def notify_order(self, is_buy_order):
        """Handle the events of executed orders."""

        if is_buy_order:
            # self.commission_on_last_purchase = order.executed.comm
            # self.log(f"Commission on Buy: {order.executed.comm}")
            # self.log('BUY EXECUTED, %.2f' % order.executed.price)  # executing.price for a buy is next bar's open price
            self.log('BUY EXECUTED, %.2f' % self.state.price_of_last_purchase)
        else:
            # Calculate cumulative profit/loss after selling
            self.state.cumulative_profit += (self.state.price_of_last_sale - self.state.price_of_last_purchase) * abs(
                self.state.order_quantity)  # - self.commission_on_last_purchase

            self.state.trading_count += 1
            self.log('SELL EXECUTED, %.2f' % self.state.price_of_last_sale)
            # print(f"total profit on trades:{self.cumulative_profit}")


class SmaCrossStrategyBt(bt.Strategy):
    params = dict(
        fast_ma_period=3,  # Period for the fast moving average
        slow_ma_period=15,  # Period for the slow moving average
        high_low_period=20,  # Period for tracking highest and lowest prices
        high_low_tolerance=0.15,  # Tolerance for approximating high or low prices
        buy_profit_threshold=2,  # Threshold to decide when to sell based on profit
        sell_profit_threshold=2,
    )

    def __init__(self):

        self.trader = AlpacaTrader()
        self.state = SmaCrossStrategyState(float(self.trader.buying_power) or constants.cash)
        self.indicators = SmaCrossStrategyIndicators(self.p, self.data)
        self.strategy = SmaCrossStrategy(self.indicators, self.state, trader=self.trader)

    def next(self):
        # self.data -> DataFrame class
        # df = self.data
        if self.cerebro.params.live:
            try:
                self.strategy.live()
            except KeyboardInterrupt:
                print("KeyboardInterrupt received. shutting down trader...")
                logging.info("KeyboardInterrupt received on live trading")
                self.trader.trading_client.cancel_orders()

        else:
            self.strategy.back_test()

    def stop(self):
        self.strategy.stop()
        # # Calculate the ROI based on the net profit and starting balance
        # self.s.total_return_on_investment = self._roi()
        # # print(f'Last sale : {self.price_of_last_sale}')
        # if self.live_mode:
        #     self.trader.trading_client.cancel_orders()
        #     # logging.info("266 -pending orders canceled")

# def main():
#     # Arrange
#     i  = Mock(indecators)
#     i.indicators.xx.return = 10;
#     t = Mock(Trader)
#     s = SmaCrossStrategy(i,t )
#
#     # Act
#     df = {
#         open: 1,
#         volume: 2
#     }
#     s.next(df)
#
#     # Assert
#
#     # Is state updated
#     s.state.trade_active == 2
#     assert.t.buy.incokes(1)
