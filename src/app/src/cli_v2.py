# Importing logger_config to set up application-wide logging and exception handling
# import logger_config


import csv
import logging
import multiprocessing

import pandas as pd

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies.src.sma.sma_cross_strategy import SmaCrossStrategy


def run_single(live=False):
    buy_profit_threshold = 1.0
    # fast_ma_period = 8
    slow_ma_period = 15

    median_volume, min_price = get_parameters(buy_profit_threshold=buy_profit_threshold, slow_ma_period=slow_ma_period)

    strategy = (
        SmaCrossStrategy,
        dict(

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

            # fast_ma_period=3,
            # slow_ma_period=10,
            # high_low_period=12,
            # high_low_tolerance=0.5,
            # buy_profit_threshold=1.0,
            # sell_profit_threshold=6,
            # buying_power=800,
            # min_price=245.65,
            # loss_value=15,
            # last_sale_price=None,
            # median_volume=18224.5

            # sep 18
            # fast_ma_period=29,
            # slow_ma_period=42,
            # high_low_period=12,
            # high_low_tolerance=0.5,
            # buy_profit_threshold=2.0,
            # sell_profit_threshold=3.5,
            # buying_power=800,
            # min_price=245.65,
            # loss_value=15,
            # last_sale_price=None,
            # median_volume=18224.5

            # # sep 20
            # fast_ma_period=8,
            # slow_ma_period=14,
            # high_low_period=25,
            # high_low_tolerance=0.5,
            # buy_profit_threshold=1.5,
            # sell_profit_threshold=1.5,
            # buying_power=800,
            # min_price=245.65,
            # loss_value=15,
            # last_sale_price=None,
            # median_volume=18224.5

            # sep 21
            # fast_ma_period=fast_ma_period,
            slow_ma_period=slow_ma_period,
            buy_profit_threshold=buy_profit_threshold,
            median_volume=median_volume,
            min_price=min_price,

            high_low_period=36,
            high_low_tolerance=0.5,
            sell_profit_threshold=3.0,
            buying_power=800,
            loss_value=15,
            last_sale_price=None,

        ))
    # strategy = (TrendLineStrategy,
    #             dict(period=10, poly_degree=2, predicted_line_length=2, line_degree=1, devfactor=1.0))

    # strategy = (DemoStrategy, {})
    result = BacktraderStrategy(live).add_strategy(strategy).run()
    logging.info(
        f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.average_return_on_investment * 100, 3)}%")

    # logging.info(
    #     f"Number of Trades: {result.state.trading_count}\nReturn on investment: {round(result.state.total_return_on_investment * 100, 3)}%")


def get_parameters(buy_profit_threshold=None, slow_ma_period=None):
    def get_stop_point(column):
        # here we get sma values
        _min_value = column.iloc[0]
        # _min_value_value_index = 0

        # here we return sell value's index of sma values in order to find buy value
        for i in range(len(column)):

            if column.iloc[i] < _min_value:
                _min_value = column.iloc[i]
                # _min_value_value_index = i
            elif _min_value + buy_profit_threshold < column.iloc[i]:
                return i
        return len(column)

    df = pd.read_csv(constants.csv_file_path)
    close = df['close'].rolling(window=slow_ma_period).mean()  # get sma

    close = close[slow_ma_period - 1:]
    df = df[slow_ma_period - 1:]
    df.reset_index(drop=True, inplace=True)  # Reset the index of the new DataFrame if needed

    stop = get_stop_point(close)
    min_value = df['close'].iloc[:stop].min()

    return df['volume'].median(), min_value


def get_sma_cross_strategy_v2_optimum_params(best_roi=0, fast_ma_period=None, slow_ma_period=None, high_low_period=None,
                                             high_low_tolerance=None,
                                             buy_profit_threshold=None, sell_profit_threshold=None, pre_count=2966):
    buying_power = 800
    loss_value = 15
    last_sale_price = None
    median_volume, min_price = get_parameters(buy_profit_threshold=buy_profit_threshold, slow_ma_period=slow_ma_period)

    p2 = None
    count = 0
    roi_count = 0
    statistics = [
        ["iteration", "Trading Count", "Roi", "Fast Period", "Slow Period", "high & low Period", "high & low Error",
         "Buy Gain Value", "Sell Gain value"]]
    try:
        for p in range(high_low_period, 50):
            p2 = p
            if p == high_low_period + 2:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(p - 2)
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                write_csv(statistics)

                raise Exception("=== Parameter Tuning successfully terminated===")
            # for pf in range(fast_ma_period, 31):
            for ps in range(slow_ma_period, 61):
                # if pf > ps:
                #     continue
                for x in range(high_low_tolerance, 6):  # ignored
                    # Dev-Factor from 1, 1.5, 2
                    e = x / 10
                    for yy in range(sell_profit_threshold, 9):
                        sgv = yy / 2
                        for y in range(buy_profit_threshold, 9):
                            bgv = y / 2
                            if count >= pre_count:
                                result = BacktraderStrategy(live=False
                                                            ).add_strategy((SmaCrossStrategy,
                                                                            dict(
                                                                                slow_ma_period=ps,
                                                                                high_low_period=p,
                                                                                high_low_tolerance=e,
                                                                                buy_profit_threshold=bgv,
                                                                                sell_profit_threshold=sgv,
                                                                                buying_power=buying_power,
                                                                                min_price=min_price,
                                                                                loss_value=loss_value,
                                                                                last_sale_price=last_sale_price,
                                                                                median_volume=median_volume, ))).run()
                                # statistics.append(
                                #     [count, result.trading_count, result.average_return_on_investment, ps, p, e,
                                #      bgv, sgv])
                                if result.average_return_on_investment > best_roi:
                                    best_roi = result.average_return_on_investment
                                    roi_count = count
                                    print(
                                        f"count : {count}\nBest ROI: {round(best_roi * 100, 3)}%\n Period Slow: {ps}\n high_low_period: {p}\n high_low_error: {e}\n Buy Gain value: {bgv}\n Sell Gain value: {sgv}")
                                print(count)
                                # print(result.total_return_on_investment)
                            count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"high_low_period: {p2}-current Count: {count}-Best ROI: {best_roi * 100}%")
        write_csv(statistics)


configurations_for_sma_cross_v2 = [
    dict(fast_ma_period=3, slow_ma_period=8, high_low_period=8, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=3, slow_ma_period=8, high_low_period=20, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    dict(fast_ma_period=3, slow_ma_period=8, high_low_period=35, high_low_tolerance=5, buy_profit_threshold=2,
         sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=22, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=14, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=16, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=18, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2),
    # dict(fast_ma_period=3, slow_ma_period=8, high_low_period=20, high_low_tolerance=5, buy_profit_threshold=2,
    #      sell_profit_threshold=2)
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
    # import logger_config
    # run_single()
    run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
