from broker.src.alpaca_trader import AlpacaTrader
from strategies.src.sma_coss_strategy_v2 import TALibSMA
import backtrader as bt

class SmaCrossStrategyState:

    def __init__(self) -> None:
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


class SmaCrossStrategyIndicators:

    def __init__(self, config, data) -> None:
        fast_moving_avg = TALibSMA(self.data, period=config.fast_ma_period)
        slow_moving_avg = TALibSMA(self.data, period=config.slow_ma_period)

        self.moving_avg_crossover_indicator = bt.ind.CrossOver(fast_moving_avg, slow_moving_avg)
        self.moving_avg_crossover_indicator.plotinfo.plot = False
        self.recorded_highest_price = bt.indicators.Highest(data.close, period=config.high_low_period)
        self.recorded_lowest_price = bt.indicators.Lowest(data.close, period=config.high_low_period)


class SmaCrossStrategy:
    def __init__(self, indicators: SmaCrossStrategyIndicators, trader = None) -> None:
        self.trader = trader
        self.state = SmaCrossStrategyState()
        self.indicators = indicators

    def next(self, data):
        pass
        # write your algorithm


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
        self.indicators = SmaCrossStrategyIndicators(self.p, self.data)
        self.strategy = SmaCrossStrategy(self.indicators, self.trader)

    def next(self):
        # self.data -> DataFrame class
        df = self.data
        self.strategy.next(df)



def main():
    # Arrange
    i  = Mock(indecators)
    i.indicators.xx.return = 10;
    t = Mock(Trader)
    s = SmaCrossStrategy(i,t )

    # Act
    df = {
        open: 1,
        volume: 2
    }
    s.next(df)

    # Assert

    # Is state updated
    s.state.trade_active == 2
    assert.t.buy.incokes(1)


