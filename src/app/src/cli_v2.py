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

    # todo don't forget to delete following in Colab
    slow_ma_period = 64
    fast_ma_period = 56
    devfactor = 2
    # high_low_period = 8
    # high_low_tolerance = 0.5
    # buy_profit_threshold = 3.5
    # sell_profit_threshold = 3.5
    median_volume, min_price = get_parameters(slow_ma_period=slow_ma_period)
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
            fast_ma_period=fast_ma_period,
            devfactor=devfactor,

            median_volume=median_volume,
            min_price=min_price,

            # buy_profit_threshold=buy_profit_threshold,
            # high_low_period=high_low_period,
            # high_low_tolerance=high_low_tolerance,
            # sell_profit_threshold=sell_profit_threshold,
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


def get_parameters(slow_ma_period=None):
    def get_stop_point(column):
        # here we get sma values
        _min_value = column.iloc[0]
        # _min_value_value_index = 0

        # here we return sell value's index of sma values in order to find buy value
        for i in range(len(column)):

            if column.iloc[i] < _min_value:
                _min_value = column.iloc[i]
                # _min_value_value_index = i
            elif _min_value + column.iloc[0] * 0.05 < column.iloc[i]:
                return i
        return len(column)

    df = pd.read_csv(constants.csv_file_path)
    close = df['close'].rolling(window=slow_ma_period).mean()  # get sma

    close = close[slow_ma_period - 1:]
    df = df[slow_ma_period - 1:]
    df.reset_index(drop=True, inplace=True)  # Reset the index of the new DataFrame if needed

    stop = get_stop_point(close)
    min_value = df['close'].iloc[:stop].min()
    median = df['volume'].median()
    logging.info(f'median ={median}--min_value={min_value}')
    return median, min_value


def get_sma_cross_strategy_v2_optimum_params(slow_ma_period=None, fast_ma_period=None,devfactor=None,start_count=None,stop_count=None):
    best_roi = 0
    buying_power = 800
    loss_value = 15
    last_sale_price = None
    median_volume, min_price = get_parameters(slow_ma_period=slow_ma_period)

    count = 1
    roi_count = 1
    statistics = {}

    header = ["iteration", "Trading Count", "Roi", "Fast Period", "Slow Period", "devfactor"]
    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # writing the header

    try:
        for pf in range(fast_ma_period, 300):
                for ps in range(slow_ma_period, 500):
                    if pf > ps:
                        continue
                    for yy in range(devfactor, 6):
                        df = yy / 2

                        if stop_count > count >= start_count:
                            result = BacktraderStrategy(live=False
                                                        ).add_strategy((SmaCrossStrategy,
                                                                        dict(
                                                                            slow_ma_period=ps,
                                                                            fast_ma_period=pf,
                                                                            devfactor=df,

                                                                            high_low_period=20,
                                                                            high_low_tolerance=0.15,
                                                                            # buy_profit_threshold=bgv,
                                                                            # sell_profit_threshold=sgv,
                                                                            buying_power=buying_power,
                                                                            min_price=min_price,
                                                                            loss_value=loss_value,
                                                                            last_sale_price=last_sale_price,
                                                                            median_volume=median_volume, ))).run()
                            statistics[result.average_return_on_investment] = [count, result.trading_count, result.average_return_on_investment,pf, ps, df]
                            if result.average_return_on_investment > best_roi:
                                best_roi = result.average_return_on_investment
                                roi_count = count
                                print(
                                    f"count : {count}\nBest ROI: {round(best_roi * 100, 3)}%\nslow_ma_period={ps}\nfast_ma_period={pf}\ndevfactor={df}")
                            print(f'{count}-{roi_count}--{best_roi}')
                            if count % 2000 == 0:
                                write_csv(statistics)
                        elif count == stop_count:

                            print(f"Last Count: {count}")
                            print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                            write_csv(statistics)

                            raise Exception("=== Parameter Tuning successfully terminated===")
                        count += 1
        print(f"Total Count: {count}-Best ROI: {best_roi * 100}% at count : {roi_count}")
        write_csv(statistics)

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"current Count: {count}-Best ROI: {best_roi * 100}% at count : {roi_count}")
        write_csv(statistics)
    except :
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"current Count: {count}-Best ROI: {best_roi * 100}% at count : {roi_count}")
        write_csv(statistics)


# configurations_for_sma_cross_v2 = [
#     dict(slow_ma_period=8, high_low_period=8, high_low_tolerance=5, buy_profit_threshold=2,
#          sell_profit_threshold=2),
#     dict(slow_ma_period=8, high_low_period=20, high_low_tolerance=5, buy_profit_threshold=2,
#          sell_profit_threshold=2),
#     dict(slow_ma_period=8, high_low_period=35, high_low_tolerance=5, buy_profit_threshold=2,
#          sell_profit_threshold=2),
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

# ]


def write_csv(statistics):
    sorted_keys = sorted(statistics.keys(), reverse=True)[:len(statistics) // 2]
    with open(constants.stat_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for key in sorted_keys:
            writer.writerow(statistics[key])  # writing each entry as a row

    statistics.clear()
    print('data written to csv')


def sma_cross_v2_config_process(config):
    return get_sma_cross_strategy_v2_optimum_params(**config)


def run_parallel(config_process=sma_cross_v2_config_process, configurations=None, start_count=0, increment=1000):

    processes = []
    if configurations is None:
        global config
        for _ in range(7):
            config['start_count'] = start_count
            config['stop_count'] = start_count = start_count + increment
            processes.append(multiprocessing.Process(target=config_process, args=(config,)))
            config = config.copy()
    # processes = [multiprocessing.Process(target=config_process, args=(config,)) for config in configurations]

    # Start processes
    for p in processes:
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    logging.info('All functions have finished executing')


config = dict(slow_ma_period=8, fast_ma_period=2, devfactor=3)

if __name__ == "__main__":
    # import logger_config
    # run_single()
    run_parallel(start_count=1, increment=100)
# run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)

