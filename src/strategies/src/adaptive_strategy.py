# '''Let's break down the efficiency of the two methods in terms of both computation and implementation:
#
# ### Using a Custom VWAP Calculation:
#
# **Pros:**
# 1. **Computational Efficiency**: It uses cumulative indicators to track the sum of volume and volume-weighted price. As a result, it doesn't need to recompute the entire VWAP for each bar and can efficiently calculate the VWAP for the new period.
# 2. **Flexibility**: Since you have control over the internals of the calculation, it's easier to introduce additional custom modifications if needed.
#
# **Cons:**
# 1. **Implementation Complexity**: Building a custom VWAP from scratch involves more lines of code and can introduce bugs if not done correctly.
# 2. **Maintenance**: If there are improvements or fixes to the built-in VWAP in future versions of Backtrader, you would not benefit from them automatically.
#
# ### Wrapping the Built-in VWAP:
#
# **Pros:**
# 1. **Implementation Simplicity**: Utilizing the built-in VWAP reduces potential bugs since the core calculation has been vetted by the Backtrader community.
# 2. **Maintenance**: As Backtrader evolves, improvements to the core VWAP will be incorporated automatically into your adaptive version.
#
# **Cons:**
# 1. **Computational Efficiency**: Dynamically updating the VWAP's period and forcing recomputation can be computationally intensive, especially with large datasets or very frequent updates.
# 2. **Less Flexibility**: If you wish to introduce more custom modifications that are not directly supported by the built-in VWAP, you might find it challenging.
#
# ### Conclusion:
#
# - If you plan to run your strategy on large datasets, especially if you expect to adjust the period frequently, the custom VWAP calculation method will be more efficient in terms of computation.
# - If you prioritize simplicity, ease of maintenance, and want to leverage the existing Backtrader infrastructure, wrapping the built-in VWAP will be more efficient in terms of development time.
#
# Ultimately, the best choice depends on your specific needs and priorities. If computational efficiency is paramount, opt for the custom method. If you value code simplicity and maintainability, the built-in method would be more suitable.'''


# class AdaptiveVWAP(bt.Indicator):
#     lines = ('vwap',)
#     params = (('period', 14),)
#
#     def __init__(self):
#         self.cum_vol = self.data.volume.clone()
#         self.cum_vol_price = (self.data.volume * self.data.close).clone()
#
#     def next(self):
#         self.cum_vol[0] = self.cum_vol[-1] + self.data.volume[0]
#         self.cum_vol_price[0] = self.cum_vol_price[-1] + (self.data.volume[0] * self.data.close[0])
#
#         self.lines.vwap[0] = self.cum_vol_price[0] / self.cum_vol[0] if self.cum_vol[0] else 0

import csv
from collections import deque

import backtrader as bt
import numpy
import numpy as np
import pandas
import talib as TA

from app.src import constants
from app.src.constants import min_price


def log_to_csv(data, filename=constants.mama_file_path):

    """Log the values to a CSV file.

    Parameters:
    - filename: the name of the CSV file.
    - iteration: iteration number or count.
    - mama: current value of MAMA.
    - fama: current value of FAMA.
    - smoothed_mama: current value of Smoothed MAMA.
    - fama_past: previous value of FAMA.
    - mama_past: previous value of MAMA.

    """

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def terminate(mes):
    raise Exception(f'terminated-{mes}')


class AdaptiveVWAP(bt.Indicator):
    """
    Adaptive Volume Weighted Average Price (VWAP) Indicator with dynamic period adjustment.

    This indicator calculates VWAP giving more importance to recent data.
    """
    lines = ('vwap',)
    params = (
        ('period', 14),
        ('adaptiveness', 0.1)  # Defines the weighting; higher value gives more importance to recent data
    )

    def __init__(self):
        """
        Initialize the AdaptiveVWAP indicator.
        """
        self.addminperiod(160)
        self.volume_weighted_price = self.data.volume * self.data.close

        # '''Simple Moving Average approach to calculating the VWAP'''
        # self.rolling_vol = bt.indicators.SumN(self.data.volume, period=self.p.period)
        # self.rolling_vol_price = bt.indicators.SumN(self.data.volume * self.data.close,

    def prenext(self):
        # If it's the first data point
        self.lines.vwap[0] = self.data.close[0]
        # print(f'pre next line.vwap: {self.lines.vwap[0]}')

    def next(self):
        """
        Update the vwap line for the current data point.
        """
        # return
        # Exponential approach for dynamic adjustment
        self.lines.vwap[0] = ((1 - self.p.adaptiveness) * self.lines.vwap[-1] +
                              self.p.adaptiveness * self.volume_weighted_price[0] / self.data.volume[0])
        # print(f'adjusted line.vwap: {self.lines.vwap[0]}')

    def adjust_adaptiveness(self, new_adaptiveness):
        """
    Adjusts the weighting or adaptiveness of the VWAP.

    Parameters:
    - new_adaptiveness (float): New value for adaptiveness.
    """
        self.p.adaptiveness = new_adaptiveness


class MAMAIndicator(bt.Indicator):
    """
    MESA Adaptive Moving Average (MAMA) and Following Adaptive Moving Average (FAMA).

    The MAMA adjusts dynamically to price behavior and is used to identify
    the direction of the trend. The FAMA, on the other hand, is used to generate
    trading signals when it crosses over or under MAMA. Both are calculated using
    a combination of Hilbert Transform and Moving Average calculations.

    Parameters:
    - fastlimit: Maximum value for the adaptive alpha smoothing factor.
    - slowlimit: Minimum value for the adaptive alpha smoothing factor.
    - smooth_period: Period for smoothed moving average (unused in the current version).

    Output Lines:
    - mama: MESA Adaptive Moving Average.
    - fama: Following Adaptive Moving Average.
    """
    lines = ('mama', 'fama')
    params = dict(period=160)

    def __init__(self):
        self.count = 0
        self.addminperiod(160)
        self.last_N_prices = deque(maxlen=self.p.period)  # Use a deque to keep the last N prices

    def prenext(self):
        self.count += 1
        print(f'mama-pre count ={self.count}')
        self.last_N_prices.append(self.data.close[0])

    def next(self):
        # return
        self.count += 1
        # print(f'mama count ={self.count}')
        # Append the current close price to the deque
        self.last_N_prices.append(self.data.close[0])

        # Convert the deque to a numpy array
        data_series = np.array(self.last_N_prices)

        df = pandas.DataFrame({
            'open': data_series,
            'close': data_series,
            'high': data_series,
            'low': data_series
        })

        # Then, use the DataFrame for TA.MAMA
        mama, fama = TA.MAMA(df['close'].values)

        # Set current values for the indicator lines
        if len(mama) != 0 and mama[-1] is not None:
            self.lines.mama[0] = mama[-1]
        else:
            self.lines.mama[0] = float('nan')

        if len(fama) != 0 and fama[-1] is not None:
            self.lines.fama[0] = fama[-1]
        else:
            self.lines.fama[0] = float('nan')


# custom implementation
# class MAMA(bt.Indicator):
#     """
#     MESA Adaptive Moving Average (MAMA) and Following Adaptive Moving Average (FAMA).
#
#     The MAMA adjusts dynamically to price behavior and is used to identify
#     the direction of the trend. The FAMA, on the other hand, is used to generate
#     trading signals when it crosses over or under MAMA. Both are calculated using
#     a combination of Hilbert Transform and Moving Average calculations.
#
#     Parameters:
#     - fastlimit: Maximum value for the adaptive alpha smoothing factor.
#     - slowlimit: Minimum value for the adaptive alpha smoothing factor.
#     - smooth_period: Period for smoothed moving average (unused in the current version).
#
#     Output Lines:
#     - mama: MESA Adaptive Moving Average.
#     - fama: Following Adaptive Moving Average.
#     """
#     lines = ('mama', 'fama')
#     params = dict(fastlimit=0.5, slowlimit=0.05, smooth_period=3)
#
#     def __init__(self):
#         self.addminperiod(7)
#         self.count = 0
#
#         # Initialize LineBuffers for historical values
#         # self.hilbert_periods = bt.LineBuffer()
#         # self.prev_phase = bt.LineBuffer()
#         # self.re = bt.LineBuffer()
#         # self.im = bt.LineBuffer()
#
#         self.hilbert_periods = deepcopy(self.data.close)  # todo change this in future
#         self.prev_phase = deepcopy(self.data.close)
#         self.re = deepcopy(self.data.close)
#         self.im = deepcopy(self.data.close)
#
#         # Initialize buffers with zeros to avoid NaN issues
#         for buffer in [self.hilbert_periods, self.prev_phase, self.re, self.im]:
#             buffer.maxlen = 7
#             buffer.addminperiod(7)  # todo remove
#             # print(f'length-{buffer.maxlen}')
#
#         for buffer in [self.hilbert_periods, self.prev_phase, self.re, self.im]:
#             for idx in range(buffer.maxlen):
#                 buffer.set(0.0, ago=idx)
#
#         # for buffer in [self.hilbert_periods, self.prev_phase, self.re, self.im]:
#         # #     for idx in range(7):
#         # #
#         # #         buffer.lines[0][idx] = 0.0
#
#         # Initialize the smoothed mama (not being used but can be used for future extensions)
#         self.smoothed_mama = bt.indicators.SmoothedMovingAverage(self.lines.mama, period=self.p.smooth_period)
#
#     def prenext(self):
#         print(f'MAMA pre-next executed-{self.count}')
#         self.count += 1
#
#     def next(self):
#         print(f'MAMA next executed-{self.count}')
#         self.count += 1
#
#         # Detrend price
#         detrender = (4 * self.data.close[0] + 3 * self.data.close[-1] + 2 * self.data.close[-2] + self.data.close[-3]) / 10
#
#         # Compute InPhase and Quadrature components
#         q1 = (detrender - self.data.close[-6]) / 2 + 0.378 * ((detrender - self.data.close[-4]) / 2)
#         i1 = self.data.close[-4] - 0.25 * (detrender + self.data.close[-7])
#
#         # Avoid divide by zero by initializing to a small number
#         self.re[0] = 0.2 * (i1 + 0.878 * self.re[-1]) + 1e-10
#         self.im[0] = 0.2 * (q1 + 0.878 * self.im[-1]) + 1e-10
#
#         # Compute phase of the cyclic component
#         phase = math.atan2(self.im[0], self.re[0]) if self.re[0] != 0 else 0.0
#         if phase < 0:
#             phase += 2 * math.pi
#
#         # Calculate delta phase and adjust for potential phase wrapping
#         delta_phase = phase - self.prev_phase[0]
#         if delta_phase > math.pi:
#             delta_phase -= 2 * math.pi
#         elif delta_phase < -math.pi:
#             delta_phase += 2 * math.pi
#
#         self.prev_phase[0] = phase
#
#         # Update the Hilbert Periods with constraints
#
#         # Break down the calculations
#         # current_hilbert = self.hilbert_periods[0] + 10 * delta_phase / math.pi + self.hilbert_periods(-1)
#         # adjusted_hilbert = current_hilbert / 2
#         #
#         # max_hilbert_limit = 1.5 * self.hilbert_periods(-1)
#         # min_hilbert_limit = 0.67 * self.hilbert_periods(-1)
#         #
#         # # Use explicit conditions for comparison
#         # if adjusted_hilbert > max_hilbert_limit:
#         #     adjusted_hilbert = max_hilbert_limit
#         # elif adjusted_hilbert < min_hilbert_limit:
#         #     adjusted_hilbert = min_hilbert_limit
#
#         # self.hilbert_periods[0] = adjusted_hilbert
#         self.hilbert_periods[0] = max(
#             min((self.hilbert_periods[0] + 10 * delta_phase / math.pi + self.hilbert_periods[-1]) / 2,
#                 1.5 * self.hilbert_periods[-1]), 0.67 * self.hilbert_periods[-1])
#
#         # Compute a dynamically smoothed period with adaptive alpha
#         alpha = ((self.p.fastlimit - self.p.slowlimit) / (
#                 1 + self.hilbert_periods[0] - self.hilbert_periods[-1]) + self.p.slowlimit)
#         alpha = min(max(alpha, self.p.slowlimit), self.p.fastlimit) ** 2
#
#         # Compute the MESA Adaptive Moving Average
#         self.lines.mama[0] = alpha * self.data.close + (1 - alpha) * self.lines.mama[-1]
#
#         # Compute the FAMA as a simple moving average of MAMA
#         self.lines.fama[0] = (self.lines.mama[0] + self.lines.mama[-1]) / 2
#         c = 0

# class ROC(bt.Indicator):
#     lines = ('roc', 'rmi')
#     params = (('period', 9), ('atr_period', 14))
#
#     def __init__(self):
#         """Initialization method for the ROC Indicator."""
#         self.addminperiod(self.p.period)
#         self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)
#
#         # Initialize logging
#         self.log = logging.getLogger(__name__)
#         # logging.basicConfig(level=logging.INFO)  # Adjust level as per need
#
#     def next(self):
#         """Calculate the ROC and RMI values."""
#         current_close = self.data.close[0]
#         prev_close = self.data.close[-self.p.period]
#
#         # Check if previous close is not zero to avoid DivisionByZero error.
#         if prev_close != 0:
#             roc_value = (current_close - prev_close) / prev_close * 100
#             self.lines.roc[0] = roc_value
#
#             # Check if atr is not zero before calculating RMI.
#             if self.atr[0] != 0:
#                 self.lines.rmi[0] = roc_value / self.atr[0]
#             else:
#                 self.lines.rmi[0] = 0
#                 self.log.warning(f"ATR is zero on date {self.data.datetime.date(0)}")
#         else:
#             self.lines.roc[0] = 0
#             self.lines.rmi[0] = 0
#             self.log.warning(f"Previous close is zero on date {self.data.datetime.date(0)}")


class AdaptiveTALibROC(bt.Indicator):
    '''thresholds (self.p.threshold) and the increment/decrement values for periods might need tuning to achieve
    desirable results in practice.'''
    lines = ('roc', 'rmi')
    params = dict(period=9, atr_period=14, adapt_period=20, threshold=0.5)

    def __init__(self):
        self.close_prices = deque(maxlen=self.p.adapt_period)
        self.high_prices = deque(maxlen=self.p.adapt_period)
        self.low_prices = deque(maxlen=self.p.adapt_period)
        self.roc_values = deque(maxlen=self.p.adapt_period)
        self.addminperiod(160)
        self.count = 0

    def prenext(self):
        self.count += 1
        # print(f'pre next roc{self.count}')
        # Warm up data
        self._append_data()
        self._calculate_indicators()

    def next(self):
        self._append_data()
        self._calculate_indicators()

        # # Adapt the periods if we have enough data
        # if len(self.roc_values) >= self.p.adapt_period:
        #     roc_std = np.std(self.roc_values)
        #
        #     # Adjust periods based on ROC volatility
        #     if roc_std > self.p.threshold:
        #         self.p.period = min(self.p.period + 1, 50)  # Maximum period of 20 for this example
        #         self.p.atr_period = min(self.p.atr_period + 1, 55)  # Maximum period of 25 for this example
        #     elif roc_std < self.p.threshold:
        #         self.p.period = max(self.p.period - 1, 8)  # Minimum period of 5 for this example
        #         self.p.atr_period = max(self.p.atr_period - 1, 10)  # Minimum period of 10 for this example

    def _append_data(self):
        close = self.data.close[0]
        high = self.data.high[0]
        low = self.data.low[0]



        self.close_prices.append(close)
        self.high_prices.append(high)
        self.low_prices.append(low)

    def _calculate_indicators(self):
        # Calculate ROC using TA-LIB


        roc_array = TA.ROC(np.array(self.close_prices), timeperiod=self.p.period)
        if not numpy.isnan(roc_array[-1]):


            self.lines.roc[0] = roc_array[-1]
            self.roc_values.append(self.lines.roc[0])

            # Calculate ATR using TA-LIB
            atr_array = TA.ATR(np.array(self.high_prices), np.array(self.low_prices), np.array(self.close_prices),
                               timeperiod=self.p.atr_period)
            atr_value = atr_array[-1]

            # Calculate RMI
            self.lines.rmi[0] = self.lines.roc[0] / atr_value if atr_value != 0 else 0
        else:
            print(f'period {self.p.period}', f'alter{self.p.atr_period}')





class AdaptiveStrategy(bt.Strategy):
    params = dict(roc_period=9, roc_atr_period=14, vwap_period=30, adjust_percentage=0.05, atr_period=14,
                  volume_factor=1.5)

    # self.vwap_period_current
    # '''Trading Efficiency: Whether the new approach (adjusting adaptiveness) or the old approach (adjusting the
    # period) is more effective in terms of trading performance would depend on backtesting results. Each approach
    # emphasizes different facets of the data: Adjusting the period effectively increases or decreases the lookback
    # window of the VWAP. Adjusting the adaptiveness changes the weighting of recent data without modifying the
    # lookback window.'''

    def __init__(self):
        self.table = [['Iteration', 'Price', 'MAMA', 'FAMA', 'FAMA_Past', 'MAMA_Past', 'ROC_RMI', 'Volume_Factor',
                      'Price_Factor']]
        self.MAMA_count = 0
        self.commission_on_last_purchase = 0
        self.total_return_on_investment = 0
        self.trading_count = 0
        self.price_of_last_sale = 0
        self.price_of_last_purchase = 0
        self.cumulative_profit = 0.0
        self.starting_balance = self.broker.get_cash()

        self.trade_active = None

        self.mama = MAMAIndicator()
        self.roc = AdaptiveTALibROC(self.data, period=self.p.roc_period, atr_period=self.p.roc_atr_period)
        self.vwap = AdaptiveVWAP(self.data, period=self.p.vwap_period)
        self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)
        self.volume_ma = bt.ind.MovingAverageSimple(self.data.volume, period=self.p.roc_period)

    def next(self):
        # terminate('326')
        self.MAMA_count += 1
        # Adjust the VWAP adaptiveness based on ATR change.
        if len(self.data) > self.p.atr_period:  # todo ensure we have enough data for ATR
            current_atr = self.atr[0]
            previous_atr = self.atr[-1]

            # Instead of changing the period, we'll adjust the adaptiveness
            if current_atr > previous_atr:  # increasing volatility
                new_adaptiveness = self.vwap.p.adaptiveness + self.p.adjust_percentage
            else:  # decreasing volatility
                new_adaptiveness = self.vwap.p.adaptiveness - self.p.adjust_percentage

            # Ensure the adaptiveness remains within a valid range [0, 1]
            new_adaptiveness = min(max(0, new_adaptiveness), 1)
            self.vwap.adjust_adaptiveness(new_adaptiveness)
        self.table.append([self.MAMA_count, self.data.close[0], self.mama.mama[0], self.mama.fama[0], self.mama.fama[-1],
                          self.mama.mama[-1], self.roc.rmi[0], self.volume_ma * self.p.volume_factor,
                          self.vwap.vwap[0]])

        # Combined Strategy Logic
        # Bullish Scenario (Buy Logic)
        if self.trade_active is False:  # trade_active being False indicates no active trades
            if self.mama.fama[0] > self.mama.mama[0] and self.mama.fama[-1] <= self.mama.mama[-1]:  # Crossing upwards
                if self.roc.rmi > 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
                    if self.data.close > self.vwap.vwap[0]:
                        self.price_of_last_purchase = self.data.close[0]
                        self.buy()
                        self.trade_active = True
                        print('buy')

        # Bearish Scenario (Sell Logic)
        elif self.trade_active:  # Assuming trade_active being True indicates an active buy trade
            if self.mama.fama[0] < self.mama.mama[0] and self.mama.fama[-1] >= self.mama.mama[-1]:  # Crossing downwards
                if  self.data.volume > self.volume_ma * self.p.volume_factor: # self.roc.rmi < 0 and
                    # if self.data.close < self.vwap.vwap[0]:
                        self.price_of_last_sale = self.data.close[0]
                        self.sell()
                        self.trade_active = False
                        print('sell')


        elif self.trade_active is None and min_price >= self.data.close:
            self.price_of_last_purchase = self.data.close[0]
            self.buy()
            self.trade_active = True
            print('buy')
        # elif self.data.close == min_price:
        #     terminate(self.data.close)
        # elif self.data.close == '131.99':
        #     terminate(self.data.close)

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        # todo add log here
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
                self.log('SELL EXECUTED, %.2f' % self.price_of_last_sale)
                print(f"total profit on trades:{self.cumulative_profit}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def stop(self):
        log_to_csv(self.table)
        # Calculate the ROI based on the net profit and starting balance
        self.total_return_on_investment = self.cumulative_profit / self.starting_balance
        # if self.live_mode:
    #     self.trader.trading_client.cancel_orders()
    #     print("pending orders canceled")

# class CombinedAdaptiveStrategy(bt.Strategy):
#     params = (
#         ('roc_period', 14),
#         ('vwap_period_initial', 14),
#         ('atr_period', 14),
#         ('volume_factor', 1.5),
#         ('adjust_percentage', 0.05),  # 5% adjustment
#     )
#
#     def __init__(self):
#         self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)
#         self.vwap_period_current = self.p.vwap_period_initial
#         self.vwap = AdaptiveVWAP(self.data, period=self.vwap_period_current)
#
#         self.roc = bt.indicators.ROC(self.data.close, period=self.p.roc_period)
#         self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.roc_period)
#
#         # Including MAMA
#         self.mama, self.fama = bt.indicators.MAMA(self.data.close)
#
#     def next(self):
#         # Adjust the VWAP period based on ATR change.
#         if len(self.data) > self.p.atr_period:  # ensure we have enough data for ATR
#             current_atr = self.atr[0]
#             previous_atr = self.atr[-1]
#
#             if current_atr > previous_atr:  # increasing volatility
#                 self.vwap_period_current -= int(self.vwap_period_current * self.p.adjust_percentage)
#             else:  # decreasing volatility
#                 self.vwap_period_current += int(self.vwap_period_current * self.p.adjust_percentage)
#
#             # Ensure the period doesn't drop below a minimum threshold (e.g., 5)
#             self.vwap_period_current = max(5, self.vwap_period_current)
#
#             # Update the VWAP with the new period
#             self.vwap = AdaptiveVWAP(self.data, period=self.vwap_period_current)
#
#         # Combined Strategy Logic
#         # Bullish Scenario
#         if self.roc > 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
#             if self.data.close > self.vwap and self.data.close > self.mama:
#                 if not self.position:
#                     self.buy()
#
#         # Bearish Scenario
#         elif self.roc < 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
#             if self.data.close < self.vwap and self.data.close < self.mama:
#                 if self.position:
#                     self.sell()
