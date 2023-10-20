import logging
import threading

import backtrader as bt
import pytz

from app.src import constants
from app.src.notify import news
from broker.src.alpaca_trader import get_trade_updates, AlpacaTrader
from strategies.src.indicators.talib_sma import TALibSMA


class BuySellIndicator(bt.Indicator):
    lines = ('buy', 'sell',)
    plotinfo = dict(subplot=False)  # Plot on the same graph
    plotlines = dict(
        buy=dict(ls='-', linewidth=5, color='g'),  # Dashed line
        sell=dict(ls='-', linewidth=5, color='r'),  # Dotted line
    )


class SmaCrossStrategy(bt.Strategy):
    params = dict(

        slow_ma_period=5,  # Period for the slow moving average
        fast_ma_period=2,
        max_min_dic={},
        buying_power=800,
        min_price=220.83,
        loss_value=10,
        last_sale_price=None,
        median_volume=15710.0
    )

    def __init__(self):
        self.trader = None
        self.live_mode = False

        self.state = _State(self.p.buying_power)
        self.indicators = _Indicators(self.p, self.data)
        self.strategy = _SmaCrossStrategy(self.indicators, self.params, self.state)

        self.starting_buying_power = self.p.buying_power
        self.max_errors = None
        self.trading_count = 0

    def next(self):

        # self.data -> DataFrame class
        # df = self.data
        if self.cerebro.params.live:
            if self.live_mode:

                try:
                    self.strategy.live()
                except KeyboardInterrupt:
                    print("KeyboardInterrupt received. shutting down trader...")
                    logging.info("KeyboardInterrupt received on live trading")
                    self.trader.trading_client.cancel_orders()

            elif self.data.close[0] == 0:
                def buy():
                    algorithm_performed_buy_order_id = self.trader.buy(self.indicators.current_price())
                    # todo create dic -> {self.state.algorithm_performed_buy_order_id : order}
                    news("I placed a buy order")
                    if self.state.algorithm_performed_buy_order_id is None:
                        news("buy order not placed to alpaca")
                    else:
                        self.state.algorithm_performed_buy_order_id.add(str(algorithm_performed_buy_order_id))
                        logging.info(
                            f'algorithm performed buy order id: {self.state.algorithm_performed_buy_order_id}')  # tested
                        # logging.debug(
                        #     f'trade_active:{self.state.trade_active}<==>profit_threshold > price_of_last_sale - close price{self.config.buy_profit_threshold} > {self.state.price_of_last_sale} - {self.indicators.current_price()}<==>close price - recorded_lowest_price < high_low_tolerance={self.indicators.current_price()} - {self.indicators._recorded_lowest_price[0]} < {self.config.high_low_tolerance}<==>ready_to_buy: {self.state.ready_to_buy},volume > median_volume ={self.indicators.current_volume()} > {self.config.median_volume} <==> moving_avg_crossover_indicator > 0 = {self.indicators.moving_avg_crossover_indicator}')

                def sell():
                    news("I placed a sell order")
                    algorithm_performed_sell_order_id = self.trader.sell(self.indicators.current_price())
                    if algorithm_performed_sell_order_id is None:
                        news("sell order not placed to alpaca")
                    else:
                        self.state.algorithm_performed_sell_order_id.add(str(algorithm_performed_sell_order_id))
                        logging.info(
                            f'263 -algorithm performed sell order id: {self.state.algorithm_performed_sell_order_id}')
                        # logging.debug(
                        #     f'trade_active:{self.state.trade_active}<==>profit_threshold > close - price_of_last_purchase{self.config.sell_profit_threshold} > {self.indicators.current_price()} - {self.state.price_of_last_purchase}<==>recorded_highest_price - close < high_low_tolerance={self.indicators._recorded_highest_price[0]} - {self.indicators.current_price()} < {self.config.high_low_tolerance}<==>ready_to_sell: {self.state.ready_to_sell},volume > median_volume ={self.indicators.current_volume()} > {self.config.median_volume} <==> moving_avg_crossover_indicator < 0 = {self.indicators.moving_avg_crossover_indicator}')

                self.strategy.buy = buy
                self.strategy.sell = sell
                self.trader = AlpacaTrader()

                self.live_mode = True
                self.state.trading_count = 0
                self.state.total_return_on_investment = 0
                self.starting_buying_power = self.trader.get_buying_power()

                self.p.median_volume = 99

                positions = self.trader.trading_client.get_all_positions()
                print(f'positions: {positions}')
                logging.info(f'Number of Positions: {len(positions)}')
                if len(positions):  # todo test
                    # this is a fake buy state if any buy orders left in Alpaca,
                    # make algorithm to sell in the future
                    self.state.ready_to_buy = False
                    self.state.trade_active = True

                    if len(positions) == 2:  # if market order and stop order exists
                        if positions[0].qty > positions[1].qty:
                            self.state.price_of_last_purchase = float(positions[0].avg_entry_price)
                            self.state.order_quantity = float(positions[0].qty)
                        else:
                            self.state.price_of_last_purchase = positions[1].avg_entry_price
                            self.state.order_quantity = float(positions[1].qty)
                    else:  # if 1 order exists
                        self.state.price_of_last_purchase = float(positions[0].avg_entry_price)
                        self.state.order_quantity = float(positions[0].qty)
                    logging.info(f'Last buy : {self.state.price_of_last_purchase}')
                else:
                    # this is a fake sell state if no any sell orders left in Alpaca
                    # make algorithm to buy in the future
                    self.state.ready_to_sell = False
                    self.state.trade_active = False
                    self.state.highest_price = self.state.price_of_last_sale = constants.last_sale_price or self.state.price_of_last_sale  # todo optimize this-> back test should find out this value

                self.strategy.trader = self.trader
                thread = threading.Thread(target=get_trade_updates, args=(self.state,))  # start trade updates
                thread.start()

            else:
                self.strategy.back_test()
        else:
            self.strategy.back_test()

    def stop(self):
        self.strategy.stop()
        self.max_errors = self.state.max_errors
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
        self.highest_price = 0

        self.roi = {}
        self.starting_buying_power = buying_power  # to be commented out
        self.order_quantity = None
        self.algorithm_performed_sell_order_id = set()
        self.algorithm_performed_buy_order_id = set()
        self.trade_active = None  # None
        self.trading_count = 0
        self.price_of_last_sale = 0
        self.price_of_last_purchase = 0
        self.max_errors = 0

        self.sell_error_list = []
        self.buy_error_list = []
        self.buy_daily_error_list = []
        self.sell_daily_error_list = []
        self.buy_date = None
        self.sell_date = None
        self.current_min = None
        self.current_max = None

        self.accepted_order = None
        self.filled_order = None


class _Indicators:

    def __init__(self, params, data):
        fast_moving_avg = TALibSMA(period=params.fast_ma_period)
        slow_moving_avg = TALibSMA(period=params.slow_ma_period)
        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)

        self.data = data
        self.moving_avg_crossover_indicator.plotinfo.plot = False
        # self.slow_moving_avg.plotinfo.subplot = False
        # self.fast_moving_avg.plotinfo.subplot = False
        self.buy_sell_ind = BuySellIndicator()

    def current_price(self):
        return self.data.close[0]

    def current_price_datetime(self):
        return bt.num2date(self.data.datetime[0]).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M:%S %p')

    def current_volume(self):
        return self.data.volume[0]


class _SmaCrossStrategy:
    def __init__(self, indicators: _Indicators, config, state: _State, trader=None):
        self.cumulative_profit = 0
        self.trader = trader
        self.config = config
        self.state = state
        self.indicators = indicators

    def initial_buy_condition(self):
        return self.state.trade_active is None and self.indicators.current_price() <= self.config.min_price

    def _buy_orders_ready_on_alpaca(self):
        return self.state.filled_order is not None \
            and self.state.filled_order['id'] in self.state.algorithm_performed_buy_order_id

    def _execute_buy_orders(self):
        # logging.info("177 -buy executed") tested
        buy_price = float(self.state.filled_order['filled_avg_price'])
        self._reset_buy_state()
        self.state.price_of_last_purchase = buy_price
        self.state.filled_order = None
        # current_balance = (previous sell -> order_quantity) * price_of_last_sale
        # order_quantity = current_balance /price
        self.state.order_quantity = int(
            self.state.order_quantity * self.state.price_of_last_sale / self.indicators.current_price())
        self.notify_order(True)

    def _sell_orders_ready_on_alpaca(self):
        return self.state.filled_order is not None \
            and self.state.filled_order['id'] in self.state.algorithm_performed_sell_order_id

    def _execute_sell_orders(self):
        logging.info("192 -sell executed")
        self.state.price_of_last_sale = float(self.state.filled_order['stop_price'])
        self._reset_sell_state()
        self.state.filled_order = None
        self.notify_order(False)

    def _need_to_cancel_buy_order(self):  # placed a buy order but hasn't executed yet
        hwm = float(self.state.accepted_order['hwm'])
        return not self.state.trade_active and self.state.accepted_order is not None \
            and hwm - self.indicators.current_price() > hwm * 0.005

    def _cancel_buy_order(self):
        self._cancel_order(self.state.accepted_order['id'])
        logging.info(f"205 -buy order placed at the price {self.state.accepted_order['hwm']} has been canceled")
        self.state.accepted_order = None

    def _need_to_cancel_sell_order(self):
        hwm = float(self.state.accepted_order['hwm'])
        return self.state.trade_active and self.state.accepted_order is not None \
            and self.indicators.current_price() - hwm > hwm * 0.005

    def _cancel_sell_order(self):
        self._cancel_order(self.state.accepted_order['id'])
        logging.info(f"213 -sell order placed at the price {self.state.accepted_order['hwm']} has been canceled")
        self.state.accepted_order = None  # todo verify the logic

    def _significant_stock_price_drop(self):
        return self.state.price_of_last_purchase is not None \
            and self.config.loss_value < self.state.price_of_last_purchase - self.indicators.current_price()

    def _halt_trading_and_alert(self):
        """
                If the price drops more than 'profit_threshold' from the bought price,
                sell immediately and stop trading.
                TODO: introduce here a sps mopeed parameter and implement for both buy and sell.
                """
        _ = self.trader.trading_client.close_all_positions(cancel_orders=True)
        # logging.info(f'119 -close_all_positions:{_}') tested
        logging.critical("immediately sold")
        self.stop()
        # tested
        raise Exception(
            f"Trading Terminated and immediately sold due to significant drop of price,\nself.config.loss_value < "
            f"price_of_last_purchase - current price = {self.config.loss_value} < "
            f"{self.state.price_of_last_purchase} - {self.indicators.current_price()}  ")

    def _conditions_met_for_buy(self):
        return self.state.trade_active is False  # todo chnage this

    def _start_buy_process(self, buy):

        if self._is_ready_to_buy_based_on_volume_and_crossover():
            buy()

            # buy indicator on plot
            self.indicators.buy_sell_ind.lines.buy[-2] = self.indicators.buy_sell_ind.lines.buy[-1] = \
                self.indicators.buy_sell_ind.lines.buy[0] = self.indicators.current_price()

    def _conditions_met_for_sell(self):
        """If a buy order has been executed, consider selling"""
        return self.state.trade_active

    def _start_sell_process(self, sell):
        if not self._is_profit():
            # logging.info('156 -active trade returned')
            return

        if self._is_ready_to_sell_based_on_volume_and_crossover():
            sell()
            self.indicators.buy_sell_ind.lines.sell[-2] = self.indicators.buy_sell_ind.lines.sell[-1] = \
                self.indicators.buy_sell_ind.lines.sell[0] = self.indicators.data.close[
                0]  # self.state.is_notified = False

    def _initial_buy(self):
        """Initiate strategy: If the current close price is below 'min_price', make the initial buy"""

        self.state.price_of_last_purchase = self.indicators.current_price()
        self.state.order_quantity = self.state.starting_buying_power / self.indicators.current_price()
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

    def _is_ready_to_buy_based_on_volume_and_crossover(self):
        """If in buy state, and volume is sufficient, and there's a positive crossover, then buy"""
        # return self.state.ready_to_buy and self.indicators.current_volume() > self.config.median_volume and self.indicators.current_price() > self.indicators.bband.lines.top[0] #and self.indicators.fast_moving_avg > self.indicators.slow_moving_avg # self.indicators.moving_avg_crossover_indicator > 0  # when seasonal and sma = price
        return self.indicators.current_volume() > self.config.median_volume and self.indicators.moving_avg_crossover_indicator > 0  # self.indicators.current_price() >self.indicators.fast_moving_avg > self.indicators.slow_moving_avg # self.indicators.current_price() < self.indicators.bband.lines.bot[0] and self.indicators.fast_moving_avg > self.indicators.slow_moving_avg # # when seasonal and sma = price

    def _is_profit(self):
        """If the gain from the bought price exceeds 'profit_threshold', continue without selling"""
        return self.state.price_of_last_purchase * 1.01 <= self.indicators.current_price()

    def _is_ready_to_sell_based_on_volume_and_crossover(self):
        """If in sell state, and volume is sufficient, and there's a negative crossover, then sell"""
        # return self.state.ready_to_sell and self.indicators.current_volume() > self.config.median_volume and self.indicators.current_price() < self.indicators.bband.lines.bot[0] #and self.indicators.fast_moving_avg < self.indicators.slow_moving_avg #  self.indicators.moving_avg_crossover_indicator < 0
        return self.indicators.current_volume() > self.config.median_volume and self.indicators.moving_avg_crossover_indicator < 0  # self.indicators.current_price() < self.indicators.fast_moving_avg < self.indicators.slow_moving_avg # and self.indicators.fast_moving_avg < self.indicators.bband.lines.top[0]

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
            self.indicators.buy_sell_ind.lines.buy[-1] = self.indicators.buy_sell_ind.lines.buy[0] = \
                self.indicators.data.close[0]

    def _check_alpaca_status(self):
        # Check and execute buy orders on alpaca
        if self._buy_orders_ready_on_alpaca():
            self._execute_buy_orders()

        # Check and execute sell orders on alpaca
        elif self._sell_orders_ready_on_alpaca():
            self._execute_sell_orders()

        # Cancel any pending buy order
        if self._need_to_cancel_buy_order():
            news(f"buy order placed at the price {self.state.accepted_order['hwm']} has been canceled")
            self._cancel_buy_order()

        # Cancel any pending sell order
        elif self._need_to_cancel_sell_order():
            news(f"the sell order placed at the price {(self.state.accepted_order['hwm'])} has been canceled")
            self._cancel_sell_order()

        # Halt trading if there's a significant drop in stock prices
        if self._significant_stock_price_drop():
            news("⚠️ The price has dropped significantly low. Trading has been stopped.")
            self._halt_trading_and_alert()

    def buy(self):
        self._reset_buy_state()
        # assume that lowest_price = last_purchase
        self.state.lowest_price = self.state.price_of_last_purchase = self.indicators.current_price()
        # current_balance = (previous sell -> order_quantity) * price_of_last_sale
        # order_quantity = current_balance /price
        # here total buying power is considered as (previous order_quantity * price_of_last_sale)we invest all money
        self.state.order_quantity = self.state.order_quantity * self.state.price_of_last_sale / self.indicators.current_price()
        self.notify_order(True)
        self.update_buy_error_list()

    def update_buy_error_list(self):
        if self.state.buy_date != self.indicators.data.datetime[0]:
            self.state.buy_date = self.indicators.data.datetime[0]
            converted_date = bt.num2date(self.indicators.data.datetime[0]). \
                replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')
            self.state.current_min = self.config.max_min_dic[converted_date][1]
            if self.state.buy_daily_error_list:
                self.state.buy_error_list.append(min(self.state.buy_daily_error_list))
                self.state.buy_daily_error_list.clear()

        self.state.buy_daily_error_list.append(self.indicators.current_price() - self.state.current_min)

    def update_sell_error_list(self):
        if self.state.sell_date != self.indicators.data.datetime[0]:
            self.state.sell_date = self.indicators.data.datetime[0]
            converted_date = bt.num2date(self.indicators.data.datetime[0]). \
                replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')
            self.state.current_max = self.config.max_min_dic[converted_date][0]
            if self.state.sell_daily_error_list:
                self.state.sell_error_list.append(min(self.state.sell_daily_error_list))
                self.state.sell_daily_error_list.clear()

        self.state.sell_daily_error_list.append(self.state.current_max - self.indicators.current_price())

    def sell(self):
        self.state.highest_price = self.state.price_of_last_sale = self.indicators.current_price()
        self._reset_sell_state()
        self.notify_order(False)
        self.update_sell_error_list()

    def back_test(self):
        # print(f'date-{self.indicators.current_price()}')

        self._start_trade(self.buy, self.sell)

        # todo should return last sell price

    def live(self):
        print(f'{self.indicators.current_price_datetime()}-{self.indicators.current_price()}')
        if self.indicators.current_price() > self.state.highest_price:
            self.state.highest_price = self.indicators.current_price()

        self._check_alpaca_status()
        self._start_trade(self.buy, self.sell)

    def stop(self):
        self.state.max_errors = (max(self.state.buy_error_list), max(self.state.sell_error_list))

    def log(self, txt, dt=None):
        """ Logging function for the strategy """
        dt = dt or self.indicators.current_price_datetime()
        logging.info(f'{dt}, {txt}')

    def notify_order(self, is_buy_order):
        """Handle the events of executed orders."""

        if is_buy_order:
            self.log('BUY EXECUTED, %.2f' % self.state.price_of_last_purchase)
        else:
            self.state.trading_count += 1
            self.cumulative_profit \
                += (self.state.price_of_last_sale - self.state.price_of_last_purchase) * self.state.order_quantity

            self.state.roi[self.indicators.current_price_datetime()] \
                = round(self.cumulative_profit / self.state.starting_buying_power, 3)

            self.log(
                'SELL EXECUTED, %.2f with quantity of %.10f' % (
                    self.state.price_of_last_sale, self.state.order_quantity))
