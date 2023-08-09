from app.src import constants
from app.src.alpaca_trader import AlpacaTrader
from strategies import SmaCrossStrategy


class LiveSmaCrossStrategy(SmaCrossStrategy):

    def __init__(self):
        super().__init__()
        self.trader = AlpacaTrader(api_key="PK167PR8HAC3D9G2XMLS",
                                   secret_key="by3sIKrZzsJdCQv7fndkAm3qabYMUruc4G67qgTA")
        self.sell_order = None
        self.buy_order = None

    def next(self):
        # 11. buy only if when order has been executed on alpaca
        if self.buy_order is not None and constants.GOOGLE_ORDER == self.buy_order:
            self.buy()
            self.trader.order_id = None
            constants.GOOGLE_ORDER = None
        # 12. sell only if when order has been executed on alpaca
        elif self.sell_order is not None and constants.GOOGLE_ORDER == self.sell_order:
            self.sell()
            constants.GOOGLE_ORDER = None
            self.trader.order_id = None

        # 1. If the price drops more than 'profit_threshold' from the bought price,
        # sell immediately and stop trading
        if self.price_of_last_purchase is not None and self.p.profit_threshold < self.price_of_last_purchase - \
                self.data.close[0]:
            self.sell_order = self.trader.sell(self.data.close[0])
            self.trader.order_id = None
            self.stop()
            return
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
                0] > constants.average_volume and self.moving_avg_crossover_indicator > 0:
                self.buy_order = self.trader.buy(self.data.close[0])
                # TrailingStopOrderRequest
                self.ready_to_buy = False
                self.order_active = True
                # =========== self.price_of_last_purchase = self.data.close[0]

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
                0] > constants.average_volume and self.moving_avg_crossover_indicator < 0:
                self.sell_order = self.trader.sell(self.data.close[0])
                self.ready_to_sell = False
                self.order_active = False
                # ===========self.price_of_last_sale = self.data.close[0]

        # 10. Initiate strategy: If the current close price is below 'min_price', make the initial buy
        elif self.order_active is None and self.data.close[0] <= constants.min_price:
            self.buy_order = self.trader.buy(self.data.close[0])
            self.trader.order_id = None
            self.ready_to_buy = False
            self.order_active = True
            # =========== self.price_of_last_purchase = self.data.close[0]
