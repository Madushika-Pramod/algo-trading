# # Importing logger_config to set up application-wide logging and exception handling
# # import logger_config
# import logger_config
# import csv
# import logging
# import multiprocessing
#
# from app.src import constants
# from app.src.back_trader import BacktraderStrategy
from strategies.src.crypto.trailing_stop_strategy import TrailingStopStrategy
#
#
# def run_single(live=False):
#     strategy = (
#         TrailingStopStrategy,
#         dict(period=120, buying_power=800)  # No Trades: 6, ROI: 10.1%
#         # dict(trail_percent_sell=1.2, trail_percent_buy=1.3, period=3, buying_power=800)  #No Trades: 5, ROI: 10.1%
#     )
#
#     # strategy = (TrailingStopStrategy, {})
#     result = BacktraderStrategy(live).add_strategy(strategy).run()
#     logging.info(
#         f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.average_return_on_investment * 100, 3)}%")
#
#
# def get_sma_cross_strategy_v2_optimum_params(best_roi=0, period=None,
#                                              pre_count=0):
#     buying_power = 800
#     count = 0
#     p2 = 0
#     t2 = 0
#     roi_count = 0
#     statistics = [
#         ["iteration", "Trading Count", "Roi", "Period", "Trail Percent Sell", "Trail Percent Buy", "Win count",
#          "Loss Count"]]
#     try:
#         for p in range(period, 500):
#             if p == period + 100:
#                 # print(
#                 #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
#                 print(p - 2)
#                 print(f"Total Count: {count}")
#                 print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
#                 write_csv(statistics)
#
#                 raise Exception("=== Parameter Tuning successfully terminated===")
#
#             if count >= pre_count:
#                 result = BacktraderStrategy(live=False).add_strategy((
#                     TrailingStopStrategy, dict(period=p,buying_power=buying_power))).run()
#                 # statistics.append(
#                 #     [count, result.trading_count, result.average_return_on_investment, p,
#                 #      result.win_count, result.loss_count])
#                 if result.average_return_on_investment > best_roi:
#                     best_roi = result.average_return_on_investment
#                     roi_count = count
#                     p2 = p
#
#                     print(
#                         f"count : {count}\nBest ROI: {round(best_roi * 100, 3)}%\nPeriod :{p}")
#                 print(count)
#                 # print(result.total_return_on_investment)
#             count += 1
#
#     except KeyboardInterrupt:
#         print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
#         print(f"p={p2}-current Count: {roi_count}-Best ROI: {best_roi * 100}%")
#     # write_csv(statistics)
#
#
# def write_csv(statistics):
#     # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]
#
#     with open(constants.stat_file_path, 'w', newline='') as file:
#         writer = csv.writer(file)
#         # writer.writerow(header)  # writing the header
#
#         for entry in statistics:
#             writer.writerow(entry)  # writing each entry as a row
#
#
# configurations_for_sma_cross_v2 = [
#     dict(period=2),
#     dict(period=102),
#     dict(period=202)
#     # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=20, high_low_tolerance=5, buy_profit_threshold=2,
#     #      sell_profit_threshold=2),
#     # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=35, high_low_tolerance=5, buy_profit_threshold=2,
#     #      sell_profit_threshold=2),
#
# ]
#
#
# def sma_cross_v2_config_process(config):
#     return get_sma_cross_strategy_v2_optimum_params(**config)
#
#
# def run_parallel(config_process, configurations):
#     # Create processes
#     processes = [multiprocessing.Process(target=config_process, args=(config,)) for config in configurations]
#
#     # Start processes
#     for p in processes:
#         p.start()
#
#     # Wait for all processes to finish
#     for p in processes:
#         p.join()
#
#     logging.info('All functions have finished executing')
#
#
# if __name__ == "__main__":
#     # run_single()
#     run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
# #
import os

# =================================================================
import backtrader as bt
from datetime import datetime

from app.src import constants
from app.src.back_trader import DataHandler


class PrevCloseIndicator(bt.Indicator):
    lines = ('prev_close',)
    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        prev_close=dict(ls='--', color='black', _plotskip='True'),
    )

    def __init__(self):
        self.addminperiod(2)

    def next(self):
        self.lines.prev_close[0] = self.data.close[-1]

class MyStrategy(bt.Strategy):
    def __init__(self):
        prev_close_ind = PrevCloseIndicator(self.data)
        # self.sma = bt.ind.KAMA(period=2)
        self.boll = bt.ind.BollingerBands(prev_close_ind, period=80, devfactor=0.5)

    def next(self):
        pass
        # print('Date:', self.data.datetime.date(0))
        # print('Current Close:', self.data.close[0])
        # print('Previous Close:', self.boll.lines.bot[-1])
        # print('Upper Band:', self.boll.lines.top[0])
        # print('Middle Band:', self.boll.lines.mid[0])
        # print('Lower Band:', self.boll.lines.bot[0])
        # print('---')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    df = DataHandler(file_path=constants.crypto_file_path).load_data()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy)
    strategies = cerebro.run()
    cerebro.plot()
# =============

