# Importing logger_config to set up application-wide logging and exception handling
# import logger_config
import logger_config
import csv
import logging
import multiprocessing

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies import SmaCrossStrategy, SmaCrossstrategyV2
from strategies.src.sma.sma_cross_strategy import SmaCrossStrategy


def run_single(live=False):
    strategy = (
        SmaCrossStrategy,
        dict(

            # fast_ma_period=14,
            # slow_ma_period=52,
            # high_low_period=20,
            # high_low_tolerance=0.3,
            # profit_threshold=2.5

            # fast_ma_period=15,
            # slow_ma_period=30,
            # high_low_period=8,
            # high_low_tolerance=0.2,
            # profit_threshold=1.0

            # fast_ma_period=16,
            # slow_ma_period=30,
            # high_low_period=8,
            # high_low_tolerance=0.2,
            # profit_threshold=1.5

            #  aug 23
            # fast_ma_period=20,
            # slow_ma_period=69,
            # high_low_period=15,
            # high_low_tolerance=0.4,
            # profit_threshold=3.0
            # aug 24
            # fast_ma_period=20,
            # slow_ma_period=25,
            # high_low_period=22,
            # high_low_tolerance=0.5,
            # profit_threshold=1.0
            # fast_ma_period=8,
            # slow_ma_period=26,
            # high_low_period=24,
            # high_low_tolerance=0.5,
            # profit_threshold=1.0
            # aug 29
            # fast_ma_period=8,
            # slow_ma_period=26,
            # high_low_period=18,
            # high_low_tolerance=0.5,
            # profit_threshold=1.0

            # #aug 30
            # fast_ma_period=6,
            # slow_ma_period=32,
            # high_low_period=22,
            # high_low_tolerance=0.5,
            # buy_profit_threshold=1.0,
            # sell_profit_threshold=1.0

            # aug 30
            # fast_ma_period=8,
            # slow_ma_period=54,
            # high_low_period=10,
            # high_low_tolerance=0.5,
            # profit_threshold=4.0

            fast_ma_period=3,
            slow_ma_period=10,
            high_low_period=12,
            high_low_tolerance=0.5,
            buy_profit_threshold=1.0,
            sell_profit_threshold=6,

        ))
    # strategy = (TrendLineStrategy,
    #             dict(period=10, poly_degree=2, predicted_line_length=2, line_degree=1, devfactor=1.0))

    # strategy = (DemoStrategy, {})
    result = BacktraderStrategy(live).add_strategy(strategy).run()
    logging.info(
        f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.total_return_on_investment * 100, 3)}%")

    # logging.info(
    #     f"Number of Trades: {result.state.trading_count}\nReturn on investment: {round(result.state.total_return_on_investment * 100, 3)}%")



def get_sma_cross_strategy_v2_optimum_params(best_roi=0, fast_ma_period=None, slow_ma_period=None, high_low_period=None,
                                             high_low_tolerance=None,
                                             buy_profit_threshold=None, sell_profit_threshold=None, pre_count=1000):
    p2 = None
    count = 0
    roi_count = 0
    statistics = [
        ["iteration", "Trading Count", "Roi", "Fast Period", "Slow Period", "high & low Period", "high & low Error",
         "Buy Gain Value", "Sell Gain value"]]
    try:
        for p in range(high_low_period, 50):
            p2 = p
            if p == high_low_period + 6:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(p - 2)
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                write_csv(statistics)

                raise Exception("=== Parameter Tunining su cessfully terminatedxx===")
            for pf in range(fast_ma_period, 31):
                for ps in range(slow_ma_period, 61):
                    if pf > ps:
                        continue
                    for x in range(high_low_tolerance, 6):
                        # Dev-Factor from 1, 1.5, 2
                        e = x / 10
                        for yy in range(sell_profit_threshold, 9):
                            sgv = yy / 2
                            for y in range(buy_profit_threshold, 9):
                                bgv = y / 2
                                # if count >= pre_count:

                                result = BacktraderStrategy(live=False
                                                            ).add_strategy((SmaCrossstrategyV2,
                                                                            dict(fast_ma_period=pf,
                                                                                 slow_ma_period=ps,
                                                                                 high_low_period=p,
                                                                                 high_low_tolerance=e,
                                                                                 buy_profit_threshold=bgv,
                                                                                 sell_profit_threshold=sgv))).run()
                                statistics.append(
                                    [count, result.trading_count, result.total_return_on_investment, pf, ps, p, e,
                                     bgv, sgv])
                                if result.total_return_on_investment > best_roi:
                                    best_roi = result.total_return_on_investment
                                    roi_count = count
                                    print(
                                        f"count : {count}\nBest ROI: {best_roi * 100}%\nPeriod fast:{pf}\n Period Slow: {ps}\n high_low_period: {p}\n high_low_error: {e}\n Buy Gain value: {bgv}\n Sell Gain value: {sgv}")
                                print(count)
                                count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...")
        print(f"high_low_period: {p2}-Total Count: {count}-Best ROI: {best_roi * 100}%")
        write_csv(statistics)


configurations_for_sma_cross_v2 = [
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=10, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=16, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=22, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=28, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=34, high_low_tolerance=5, buy_profit_threshold=2,
             sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=40, high_low_tolerance=5, buy_profit_threshold=2,
             sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=46, high_low_tolerance=5, buy_profit_threshold=2,
             sell_profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=52, high_low_tolerance=5, buy_profit_threshold=2,
             sell_profit_threshold=2)
    #      pre_count=36587),
    # dict(fast_ma_period=2, slow_ma_period=3, high_low_period=8, high_low_tolerance=2, profit_threshold=2,
    #      pre_count=36585),
    # dict(fast_ma_period=2, slow_ma_period=3, high_low_period=22, high_low_tolerance=2, profit_threshold=2,
    #      pre_count=36164)

]


def write_csv(statistics):
    # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]

    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(header)  # writing the header

        for entry in statistics:
            writer.writerow(entry)  # writing each entry as a row


def sma_cross_v2_config_process(config):
    return get_sma_cross_strategy_v2_optimum_params(**config)


def run_parallel(config_process, configurations):
    # Create processes
    processes = [multiprocessing.Process(target=config_process, args=(config,)) for config in configurations]

    # Start processes
    for p in processes:
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    logging.info('All functions have finished executing')


if __name__ == "__main__":
    run_single()
    # run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
