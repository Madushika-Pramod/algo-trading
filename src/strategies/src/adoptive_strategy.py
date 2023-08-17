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

import math

import backtrader as bt

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

# '''VWAP (Volume Weighted Average Price):
#
# Useful for institutional traders to compare their buy/sell order prices against. It gives an average price a security
# has traded at throughout the day, based on both volume and price.'''


class AdaptiveVWAP(bt.Indicator):
    # '''Backtrader's bt.indicators.SumN is an N-period sum, not a cumulative sum. So, using it would provide a rolling
    # sum over N periods, which could be employed for a rolling VWAP but wouldn't be cumulative.'''
    lines = ('vwap',)
    params = (('period', 14),)

    def __init__(self):
        self.cum_vol = bt.indicators.SumN(self.data.volume, period=self.p.period)
        self.cum_vol_price = bt.indicators.SumN(self.data.volume * self.data.close, period=self.p.period)

    def next(self):
        self.lines.vwap[0] = self.cum_vol_price[0] / self.cum_vol[0] if self.cum_vol[0] else 0


class MAMA(bt.Indicator):
    lines = ('mama', 'fama')
    params = (
        ('fastlimit', 0.5),
        ('slowlimit', 0.05),
        ('smooth_period', 3),
    )

    def __init__(self):
        self.hilbert_periods = 0
        self.prev_phase = 0
        self.re = 0
        self.im = 0
        self.counter = 0
        self.smoothed_mama = bt.indicators.SmoothedMovingAverage(self.lines.mama, period=self.p.smooth_period)

    def next(self):
        # Detrend price
        detrender = (4 * self.data.close + 3 * self.data.close(-1) + 2 * self.data.close(-2) + self.data.close(-3)) / 10

        # Compute InPhase and Quadrature components
        q1 = (detrender - self.data.close(-6)) / 2 + 0.378 * ((detrender - self.data.close(-4)) / 2)
        i1 = self.data.close(-4) - 0.25 * (detrender + self.data.close(-7))
        self.re = 0.2 * (i1 + 0.878 * self.re)
        self.im = 0.2 * (q1 + 0.878 * self.im)

        # Compute phase of the cyclic component
        phase = math.atan(self.im / self.re) if self.re != 0 else 0.0

        # Calculate delta phase
        delta_phase = self.prev_phase - phase
        self.prev_phase = phase
        self.hilbert_periods += 10 * delta_phase / math.pi
        self.hilbert_periods = (self.hilbert_periods + self.hilbert_periods(-1)) / 2
        self.hilbert_periods = max(min(self.hilbert_periods, 1.5 * self.hilbert_periods(-1)),
                                   0.67 * self.hilbert_periods(-1))

        # Compute a dynamically smoothed period
        alpha = (self.p.fastlimit - self.p.slowlimit) / (
                1 + self.hilbert_periods - self.hilbert_periods(-1)) + self.p.slowlimit
        alpha = alpha * alpha

        # Compute the MESA Adaptive Moving Average
        self.lines.mama[0] = alpha * self.data.close + (1 - alpha) * self.lines.mama(-1)
        self.lines.fama[0] = 0.5 * (1 + alpha) * self.lines.mama - (1 - alpha) * self.lines.fama(-1)


class EnhancedROC(bt.Indicator):
    lines = ('roc', 'rmi')
    params = (('period', 9), ('atr_period', 14))

    def __init__(self):
        self.addminperiod(self.params.period)
        self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)

    def next(self):
        roc_value = (self.data.close[0] - self.data.close[-self.params.period]) / self.data.close[
            -self.params.period] * 100
        self.lines.roc[0] = roc_value
        self.lines.rmi[0] = roc_value / self.atr[0]  # Normalize ROC by volatility


class EnhancedCombinedAdaptiveStrategy(bt.Strategy):
    params = (
        ('mama_fastlimit', 0.5),
        ('mama_slowlimit', 0.05),
        ('roc_period', 9),
        ('roc_atr_period', 14),
        ('mama_smooth_period', 3),
        ('vwap_period', 30),
        ('adjust_percentage', 0.05),
        ('atr_period', 14),
        ('volume_factor', 1.5)
    )

    def __init__(self):
        self.mama = MAMA(self.data.close,
                         fastlimit=self.p.mama_fastlimit,
                         slowlimit=self.p.mama_slowlimit,
                         smooth_period=self.p.mama_smooth_period)

        self.roc = EnhancedROC(self.data.close,
                               period=self.p.roc_period,
                               atr_period=self.p.roc_atr_period)
        self.vwap = AdaptiveVWAP(self.data, period=self.p.vwap_period)
        self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)
        self.vwap_period_current = self.p.vwap_period
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.roc_period)

    def next(self):
        # Adjust the VWAP period based on ATR change.
        if len(self.data) > self.p.atr_period:  # ensure we have enough data for ATR
            current_atr = self.atr[0]
            previous_atr = self.atr[-1]

            if current_atr > previous_atr:  # increasing volatility
                self.vwap_period_current -= int(self.vwap_period_current * self.p.adjust_percentage)
            else:  # decreasing volatility
                self.vwap_period_current += int(self.vwap_period_current * self.p.adjust_percentage)

            # Ensure the period doesn't drop below a minimum threshold (e.g., 5)
            self.vwap_period_current = max(5, self.vwap_period_current)

            # Update the VWAP with the new period
            self.vwap = AdaptiveVWAP(self.data, period=self.vwap_period_current)

        # Combined Strategy Logic
        # Bullish Scenario
        if self.roc.rmi > 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
            if self.data.close > self.vwap and self.data.close > self.mama.smoothed_mama:
                if not self.position:
                    self.buy()

        # Bearish Scenario
        elif self.roc.rmi < 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
            if self.data.close < self.vwap and self.data.close < self.mama.smoothed_mama:
                if self.position:
                    self.sell()


class CombinedAdaptiveStrategy(bt.Strategy):
    params = (
        ('roc_period', 14),
        ('vwap_period_initial', 14),
        ('atr_period', 14),
        ('volume_factor', 1.5),
        ('adjust_percentage', 0.05),  # 5% adjustment
    )

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.atr_period)
        self.vwap_period_current = self.p.vwap_period_initial
        self.vwap = AdaptiveVWAP(self.data, period=self.vwap_period_current)

        self.roc = bt.indicators.ROC(self.data.close, period=self.p.roc_period)
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.p.roc_period)

        # Including MAMA
        self.mama, self.fama = bt.indicators.MAMA(self.data.close)

    def next(self):
        # Adjust the VWAP period based on ATR change.
        if len(self.data) > self.p.atr_period:  # ensure we have enough data for ATR
            current_atr = self.atr[0]
            previous_atr = self.atr[-1]

            if current_atr > previous_atr:  # increasing volatility
                self.vwap_period_current -= int(self.vwap_period_current * self.p.adjust_percentage)
            else:  # decreasing volatility
                self.vwap_period_current += int(self.vwap_period_current * self.p.adjust_percentage)

            # Ensure the period doesn't drop below a minimum threshold (e.g., 5)
            self.vwap_period_current = max(5, self.vwap_period_current)

            # Update the VWAP with the new period
            self.vwap = AdaptiveVWAP(self.data, period=self.vwap_period_current)

        # Combined Strategy Logic
        # Bullish Scenario
        if self.roc > 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
            if self.data.close > self.vwap and self.data.close > self.mama:
                if not self.position:
                    self.buy()

        # Bearish Scenario
        elif self.roc < 0 and self.data.volume > self.volume_ma * self.p.volume_factor:
            if self.data.close < self.vwap and self.data.close < self.mama:
                if self.position:
                    self.sell()
