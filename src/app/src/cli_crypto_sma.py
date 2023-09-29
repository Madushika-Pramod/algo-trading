# Importing logger_config to set up application-wide logging and exception handling
# import logger_config
import csv
import logging
import multiprocessing

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies.src.crypto.sma_strategy import SmaStrategy


def run_single(live=False):
    strategy = (
        SmaStrategy,
        dict(slow_period=3, fast_period=4, buying_power=800)  # No Trades: 6, ROI: 10.1%
        # dict(trail_percent_sell=1.2, trail_percent_buy=1.3, period=3, buying_power=800)  #No Trades: 5, ROI: 10.1%
    )

    # strategy = (TrailingStopStrategy, {})
    result = BacktraderStrategy(live).add_strategy(strategy).run()
    logging.info(
        f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.average_return_on_investment * 100, 3)}%")


def get_sma_cross_strategy_v2_optimum_params(best_roi=0, slow_period=None, fast_period=None, profit_threshold=None,
                                             pre_count=0):
    buying_power = 800
    count = 0
    f2 = 0
    s2 = 0
    roi_count = 0
    # statistics = [
    #     ["iteration", "Trading Count", "Roi", "Period", "Trail Percent Sell", "Trail Percent Buy", "Win count",
    #      "Loss Count"]]
    try:
        for f in range(fast_period, 50):
            if f == fast_period + 10:
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                # write_csv(statistics)

                raise Exception("=== Parameter Tuning successfully terminated===")
            for s in range(slow_period, 50):
                if s > f:

                    if count >= pre_count:
                        result = BacktraderStrategy(live=False).add_strategy((
                            SmaStrategy,
                            dict(slow_period=s, fast_period=f, buying_power=buying_power))).run()
                        # statistics.append(
                        #     [count, result.trading_count, result.average_return_on_investment, p, ts, tb,
                        #      result.win_count, result.loss_count])
                        if result.average_return_on_investment > best_roi:
                            best_roi = result.average_return_on_investment
                            roi_count = count
                            f2 = f
                            s2 = s

                            print(
                                f"count : {count}\nBest ROI: {round(best_roi * 100, 3)}%\nFast Period :{f}\n Slow Period : {s}")
                        print(count)
                        # print(result.total_return_on_investment)
                    count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"-fast period: {f2}-Slow period: {s2}-current Count: {roi_count}-Best ROI: {best_roi * 100}%")
        # write_csv(statistics)


def write_csv(statistics):
    # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]

    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(header)  # writing the header

        for entry in statistics:
            writer.writerow(entry)  # writing each entry as a row


configurations_for_sma_cross_v2 = [
    dict(slow_period=2, fast_period=2),
    dict(slow_period=2, fast_period=22),
    dict(slow_period=2, fast_period=12)
    # ... other configurations
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
    # run_single(live=True)
    run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
