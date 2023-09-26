# Importing logger_config to set up application-wide logging and exception handling
# import logger_config
import logger_config
import csv
import logging
import multiprocessing

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies.src.crypto.trailing_stop_strategy import TrailingStopStrategy
from strategies.src.sma.sma_cross_strategy import SmaCrossStrategy


def run_single(live=False):
    strategy = (
        TrailingStopStrategy,
        dict(trail_percent_sell=0.1,trail_percent_buy=0.3, period=4, buying_power=800))
    # strategy = (TrendLineStrategy,
    #             dict(period=10, poly_degree=2, predicted_line_length=2, line_degree=1, devfactor=1.0))

    # strategy = (TrailingStopStrategy, {})
    result = BacktraderStrategy(live).add_strategy(strategy).run()
    logging.info(
        f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.total_return_on_investment * 100, 3)}%")


def get_sma_cross_strategy_v2_optimum_params(best_roi=0, trail_percent_sell=None,trail_percent_buy=None, period=None, pre_count=0):
    buying_power = 800
    count = 0
    p2=0
    t2=0
    t3=0
    roi_count = 0
    statistics = [["iteration", "Trading Count", "Roi", "Period", "Trail Percent Sell", "Trail Percent Buy", "Win count", "Loss Count"]]
    try:
        for p in range(period, 60):
            if p == period + 20:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(p - 2)
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                write_csv(statistics)

                raise Exception("=== Parameter Tuning successfully terminated===")
            for tt in range(trail_percent_sell, 10):
                ts = tt/10
                for bb in range(trail_percent_buy, 10):
                    tb = bb / 10

                    if count >= pre_count:
                        result = BacktraderStrategy(live=False).add_strategy((
                            TrailingStopStrategy, dict(trail_percent_sell=ts, trail_percent_buy=tb, period=p, buying_power=buying_power))).run()
                        statistics.append(
                            [count, result.trading_count, result.total_return_on_investment, p, ts, tb,
                             result.win_count, result.loss_count])
                        if result.total_return_on_investment > best_roi:
                            best_roi = result.total_return_on_investment
                            roi_count = count
                            p2 = p
                            t2 = ts
                            print(
                                f"count : {count}\nBest ROI: {round(best_roi * 100, 3)}%\nPeriod :{p}\n Trail Percent sell: {ts}\n Trail Percent buy: {tb}")
                        print(count)
                    # print(result.total_return_on_investment)
                    count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"period: {p2}-Trail Percent: {t2}-current Count: {roi_count}-Best ROI: {best_roi * 100}%")
        write_csv(statistics)

def write_csv(statistics):
    # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]

    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(header)  # writing the header

        for entry in statistics:
            writer.writerow(entry)  # writing each entry as a row


configurations_for_sma_cross_v2 = [
    dict(trail_percent_sell=1, trail_percent_buy=1, period=2),
    dict(trail_percent_sell=1, trail_percent_buy=1, period=22),
    dict(trail_percent_sell=1, trail_percent_buy=1, period=42)
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=20, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=35, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),

]


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
