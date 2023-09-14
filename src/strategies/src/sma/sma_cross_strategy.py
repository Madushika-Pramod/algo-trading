import logging
import threading

import backtrader as bt

from app.src import constants
from app.src.notify import news
from broker.src.alpaca_trader import get_trade_updates, AlpacaTrader
from strategies.src.indicators.talib_sma import TALibSMA


class SmaCrossStrategy(bt.Strategy):
    params = dict(
        fast_ma_period=3,  # Period for the fast moving average
        slow_ma_period=15,  # Period for the slow moving average
        high_low_period=20,  # Period for tracking highest and lowest prices
        high_low_tolerance=0.15,  # Tolerance for approximating high or low prices
        buy_profit_threshold=2,  # Threshold to decide when to sell based on profit
        sell_profit_threshold=2,
        buying_power=800,
        min_price=220.83,
        loss_value=10,
        last_sale_price=None,
        median_volume=15710.0
    )

    def __init__(self):
        self.trader = AlpacaTrader()
        # self.state = _State(self.trader.get_buying_power() or self.p.buying_power)
        self.live_mode = False
        self.starting_buying_power = self.p.buying_power
        self.state = _State(self.p.buying_power)
        self.indicators = _Indicators(self.p, self.data)
        self.strategy = _SmaCrossStrategy(self.indicators, self.params, self.state, trader=self.trader)

        self.total_return_on_investment = 0
        self.trading_count = 0

    def next(self):
        # self.data -> DataFrame class
        # df = self.data
        if self.live_mode:
            try:
                self.strategy.live()
            except KeyboardInterrupt:
                print("KeyboardInterrupt received. shutting down trader...")
                logging.info("KeyboardInterrupt received on live trading")
                self.trader.trading_client.cancel_orders()

        elif self.data.close[0] == 0:

            logging.info(f'Last sale : {self.state.price_of_last_sale}')
            logging.info(
                f"Number of Trades: {self.state.trading_count}\nReturn on investment: {round((self.state.cumulative_profit / self.starting_buying_power) * 100, 3)}%")

            self.live_mode = True
            self.state.trading_count = 0
            self.state.total_return_on_investment = 0
            self.starting_buying_power = self.trader.get_buying_power()

            # self.trader = AlpacaTrader()
            # self.starting_balance = float(self.trader.cash)

            self.p.median_volume = 99

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
                                                                                                   1].qty else \
                    positions[
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
                self.state.price_of_last_sale = constants.last_sale_price  # todo optimize this-> back test should find out this value
            thread = threading.Thread(target=get_trade_updates, args=(self.state,))  # start trade updates
            thread.start()

        else:
            self.strategy.back_test()

    def stop(self):

        # Calculate the ROI based on the net profit and starting balance
        self.total_return_on_investment = self.state.cumulative_profit / self.starting_buying_power
        self.trading_count = self.state.trading_count

        # # print(f'Last sale : {self.price_of_last_sale}')
        # if self.live_mode:
        #     self.trader.trading_client.cancel_orders()
        #     # logging.info("266 -pending orders canceled")

    def notify_order(self, order):
        super().notify_order(order)

    def notify_trade(self, trade):
        super().notify_trade(trade)


class _State:

    def __init__(self, buying_power):
        self.cumulative_profit = 0
        self.starting_balance = buying_power  # to be commented out
        self.order_quantity = None
        self.algorithm_performed_sell_order_id = None
        self.algorithm_performed_buy_order_id = None
        self.trade_active = None  # None
        self.trading_count = 0
        self.commission_on_last_purchase = 0
        self.price_of_last_sale = 0
        self.price_of_last_purchase = 0
        self.ready_to_buy = False
        self.ready_to_sell = False
        self.pending_order = None
        self.accepted_order = None
        self.market_buy_order = False

        self.is_notified = False


class _Indicators:

    def __init__(self, params, data):
        fast_moving_avg = TALibSMA(data, period=params.fast_ma_period)
        slow_moving_avg = TALibSMA(data, period=params.slow_ma_period)

        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)
        self._recorded_highest_price = bt.indicators.Highest(data.close, period=params.high_low_period)
        self._recorded_lowest_price = bt.indicators.Lowest(data.close, period=params.high_low_period)
        self._data = data

    def current_price(self):
        return self._data.close[0]

    def current_price_datetime(self):
        return bt.num2date(self._data.datetime[0])

    def current_volume(self):
        return self._data.volume[0]

    def current_highest_price(self):
        return self._recorded_highest_price[0]

    def current_lowest_price(self):
        return self._recorded_lowest_price[0]


class _SmaCrossStrategy:
    def __init__(self, indicators: _Indicators, config, state: _State, trader=None):
        self.trader = trader
        self.config = config
        self.state = state
        self.indicators = indicators

    def initial_buy_condition(self):
        return self.state.trade_active is None and self.indicators.current_price() <= self.config.min_price

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
            self.state.order_quantity * self.state.price_of_last_sale / self.indicators.current_price())
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

    def _need_to_cancel_buy_order(self):  # placed a buy order but hasn't executed yet
        return not self.state.trade_active and self.state.pending_order is not None and float(
            self.state.pending_order['hwm']) - self.indicators.current_price() > self.config.buy_profit_threshold / 4

    def _cancel_buy_order(self):
        self._cancel_order(self.state.pending_order['id'])
        logging.info(f"205 -buy order placed at the price {self.state.pending_order['hwm']} has been canceled")
        self.state.pending_order = None

    def _need_to_cancel_sell_order(self):
        return self.state.trade_active and self.state.pending_order is not None and self.indicators.current_price() - float(
            self.state.pending_order['hwm']) > self.config.sell_profit_threshold / 4

    def _cancel_sell_order(self):
        self._cancel_order(self.state.pending_order['id'])
        logging.info(f"213 -sell order placed at the price {self.state.pending_order['hwm']} has been canceled")
        self.state.pending_order = None  # todo verify the logic

    def _significant_stock_price_drop(self):
        return self.state.price_of_last_purchase is not None and self.config.loss_value < self.state.price_of_last_purchase - \
            self.indicators.current_price()

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
            f"Trading Terminated and immediately sold due to significant drop of price,\nbuy_profit_threshold * 4 < "
            f"price_of_last_purchase - current price = {self.config.buy_profit_threshold} x 4 < "
            f"{self.state.price_of_last_purchase} - {self.indicators.current_price()}  ")

    def _conditions_met_for_buy(self):
        return self.state.trade_active is False  # todo chnage this

    def _start_buy_process(self, buy):
        """If there's no existing buy order, consider buying"""
        if self._is_prior_sell_price_close_to_current():
            # logging.info('130 -inactive trade returned')
            return

        if self._is_price_near_lowest():
            self.state.ready_to_buy = True
            if not self.state.is_notified:
                # news("I'm ready to place a buy order")
                self.state.is_notified = True
            # logging.info('239 -ready_to_buy = True')
        else:
            self.state.ready_to_buy = False
            if self.state.is_notified:
                # news("I decided to not to place")
                self.state.is_notified = False
            # logging.info('241 -ready_to_buy = False')

        if self._is_ready_to_buy_based_on_volume_and_crossover():
            buy()
            self.state.is_notified = False
        # if self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():
        #     news("I placed a buy order")
        #     self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.current_price())
        #     logging.debug(f'242 -buy id: {self.state.algorithm_performed_buy_order_id}')
        #     logging.debug(f'trade_active:{self.state.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.config.buy_profit_threshold} > {self.state.price_of_last_sale} - {self.indicators.current_price()}<==>close price - recorded_lowest_price < high_low_tolerance={self.indicators.current_price()} - {self.indicators.recorded_lowest_price[0]} < {self.config.high_low_tolerance}<==>ready_to_buy: {self.state.ready_to_buy},volume > median_volume ={self.state.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator > 0 = {self.indicators.moving_avg_crossover_indicator}')
        # if not self.live_mode and self._is_ready_to_buy_based_on_volume_and_crossover():
        #     self.buy()
        #     self._reset_buy_state()
        #     self.state.price_of_last_purchase = self.indicators.current_price()

    def _conditions_met_for_sell(self):
        """If a buy order has been executed, consider selling"""
        return self.state.trade_active

    def _start_sell_process(self, sell):
        if not self._is_profit():
            # logging.info('156 -active trade returned')
            return

        if self._is_price_near_highest():
            self.state.ready_to_sell = True
            if not self.state.is_notified:
                # news("I'm ready to place a sell order")
                self.state.is_notified = True
            # logging.info('255 -ready_to_sell = True')
        else:
            self.state.ready_to_sell = False
            if self.state.is_notified:
                # news("I decided to not to place")
                self.state.is_notified = False
            # logging.info('258 -ready_to_sell = False')

        if self._is_ready_to_sell_based_on_volume_and_crossover():
            sell()
            self.state.is_notified = False
        # if self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
        #     news("I placed a sell order")
        #     self.state.algorithm_performed_sell_order_id = self.trader.sell(self.indicators.current_price())  # this step executing
        #     logging.debug(f'263 -sell id: {self.state.algorithm_performed_sell_order_id}')
        #     logging.debug(
        #         f'trade_active:{self.state.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.config.sell_profit_threshold} > {self.indicators.current_price()} - {self.state.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.recorded_highest_price[0]} - {self.indicators.current_price()} < {self.config.high_low_tolerance}<==>ready_to_sell: {self.state.ready_to_sell},volume > median_volume ={self.state.data.volume[0]} > {median_volume} <==> moving_avg_crossover_indicator < 0 = {self.indicators.moving_avg_crossover_indicator}')
        #
        # elif not self.live_mode and self._is_ready_to_sell_based_on_volume_and_crossover():
        #     self.state.price_of_last_sale = self.indicators.current_price()
        #     self.sell()
        #     self._reset_sell_state()

    def _initial_buy(self):
        """Initiate strategy: If the current close price is below 'min_price', make the initial buy"""

        self.state.price_of_last_purchase = self.indicators.current_price()
        self.state.order_quantity = self.state.starting_balance / self.indicators.current_price()
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
        return self.state.price_of_last_sale is not None \
            and self.config.buy_profit_threshold > self.state.price_of_last_sale - self.indicators.current_price()

    def _is_price_near_lowest(self):
        """Enter into buy state if the close price is near the lowest price"""
        return self.indicators.current_price() - self.indicators.current_lowest_price() < self.config.high_low_tolerance

    def _is_ready_to_buy_based_on_volume_and_crossover(self):
        """If in buy state, and volume is sufficient, and there's a positive crossover, then buy"""
        return self.state.ready_to_buy and self.indicators.current_volume() > self.config.median_volume and self.indicators.moving_avg_crossover_indicator > 0

    def _is_profit(self):
        """If the gain from the bought price exceeds 'profit_threshold', continue without selling"""
        return self.config.sell_profit_threshold <= self.indicators.current_price() - self.state.price_of_last_purchase

    def _is_price_near_highest(self):
        """Enter into sell state if the close price is near the highest price"""
        return self.indicators.current_highest_price() - self.indicators.current_price() <= self.config.high_low_tolerance

    def _is_ready_to_sell_based_on_volume_and_crossover(self):
        """If in sell state, and volume is sufficient, and there's a negative crossover, then sell"""
        return self.state.ready_to_sell and self.indicators.current_volume() > self.config.median_volume and self.indicators.moving_avg_crossover_indicator < 0

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
            # self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.current_price())
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
            news(f"buy order placed at the price {self.state.pending_order['hwm']} has been canceled")
            self._cancel_buy_order()

        # Cancel any pending sell order
        elif self._need_to_cancel_sell_order():
            news(f"the sell order placed at the price {(self.state.pending_order['hwm'])} has been canceled")
            self._cancel_sell_order()

        # Halt trading if there's a significant drop in stock prices
        if self._significant_stock_price_drop():
            news("⚠️ The price has dropped significantly low. Trading has been stopped.")
            self._halt_trading_and_alert()

    def back_test(self):
        # print(f'date-{self.indicators.current_price()}')
        def buy():
            self._reset_buy_state()
            self.state.price_of_last_purchase = self.indicators.current_price()
            # current_balance = (previous sell -> order_quantity) * price_of_last_sale
            # order_quantity = current_balance /price
            # here total buying power is considered as (previous order_quantity * price_of_last_sale)we invest all money
            self.state.order_quantity = self.state.order_quantity * self.state.price_of_last_sale / self.indicators.current_price()
            self.notify_order(True)

        def sell():
            self.state.price_of_last_sale = self.indicators.current_price()
            self._reset_sell_state()
            self.notify_order(False)

        self._start_trade(buy, sell)

        # todo should return last sell price

    def live(self):
        print(f'{self.indicators.current_price_datetime()}-{self.indicators.current_price()}')
        # self.config.median_volume = 99
        # positions = self.trader.trading_client.get_all_positions()
        # logging.info(f'Number of Positions: {len(positions)}')
        # if len(positions):  # todo test
        #     # this is a fake buy state if any buy orders left in Alpaca,
        #     # make algorithm to sell in the future
        #     self.state.ready_to_buy = False
        #     self.state.trade_active = True
        #
        #     if len(positions) == 2:  # if market order and stop order exists
        #         self.state.price_of_last_purchase = float(positions[0].avg_entry_price) if positions[0].qty > \
        #                                                                                    positions[
        #                                                                                        1].qty else positions[
        #             1].avg_entry_price
        #     else:  # if 1 order exists
        #         self.state.price_of_last_purchase = float(positions[0].avg_entry_price)
        #     logging.info(f'Last buy : {self.state.price_of_last_purchase}')
        # else:
        #     # this is a fake sell state if no any sell orders left in Alpaca
        #     # make algorithm to buy in the future
        #     self.state.ready_to_sell = False
        #     self.state.trade_active = False
        #     # initially, make algorithm to ignore profit_threshold
        #     self.state.price_of_last_sale = self.config.last_sale_price or self.state.price_of_last_sale  # todo optimize this-> back test should find out this value
        #

        # todo turn this to an event

        def buy():
            news("I placed a buy order")
            self.state.algorithm_performed_buy_order_id = self.trader.buy(self.indicators.current_price())
            # todo create dic -> {self.state.algorithm_performed_buy_order_id : order}
            logging.info(f'242 -buy id: {self.state.algorithm_performed_buy_order_id}')
            logging.debug(
                f'trade_active:{self.state.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.config.buy_profit_threshold} > {self.state.price_of_last_sale} - {self.indicators.current_price()}<==>close price - recorded_lowest_price < high_low_tolerance={self.indicators.current_price()} - {self.indicators._recorded_lowest_price[0]} < {self.config.high_low_tolerance}<==>ready_to_buy: {self.state.ready_to_buy},volume > median_volume ={self.indicators.current_volume()} > {self.config.median_volume} <==> moving_avg_crossover_indicator > 0 = {self.indicators.moving_avg_crossover_indicator}')

        def sell():
            news("I placed a sell order")
            self.state.algorithm_performed_sell_order_id = self.trader.sell(
                self.indicators.current_price())  # this step executing

            logging.debug(f'263 -sell id: {self.state.algorithm_performed_sell_order_id}')
            logging.debug(
                f'trade_active:{self.state.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.config.sell_profit_threshold} > {self.indicators.current_price()} - {self.state.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.indicators._recorded_highest_price[0]} - {self.indicators.current_price()} < {self.config.high_low_tolerance}<==>ready_to_sell: {self.state.ready_to_sell},volume > median_volume ={self.indicators.current_volume()} > {self.config.median_volume} <==> moving_avg_crossover_indicator < 0 = {self.indicators.moving_avg_crossover_indicator}')

        self._check_alpaca_status()
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
        dt = dt or self.indicators.current_price_datetime()
        logging.info(f'{dt.isoformat()}, {txt}')

    def notify_order(self, is_buy_order):
        """Handle the events of executed orders."""

        if is_buy_order:
            # self.commission_on_last_purchase = order.executed.comm
            # self.log(f"Commission on Buy: {order.executed.comm}")
            # self.log('BUY EXECUTED, %.2f' % order.executed.price)  # executing.price for a buy is next bar's open price
            self.log('BUY EXECUTED, %.2f' % self.state.price_of_last_purchase)
        else:
            self.state.trading_count += 1
            self.state.cumulative_profit += (self.state.price_of_last_sale - self.state.price_of_last_purchase) * self.state.order_quantity

            self.log('SELL EXECUTED, %.2f with quantity of %.10f' % (
                self.state.price_of_last_sale, self.state.order_quantity))

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
