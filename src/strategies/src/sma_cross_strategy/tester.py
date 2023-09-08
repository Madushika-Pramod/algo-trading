class Tester():
    def __init__(self, trader=None):
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
        self.live_mode = False