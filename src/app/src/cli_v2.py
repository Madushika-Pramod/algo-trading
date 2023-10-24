# Importing logger_config to set up application-wide logging and exception handling
# import logger_config


import csv
import logging
import multiprocessing

import pandas as pd

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies.src.sma.sma_cross_strategy import SmaCrossStrategy


def run_single(slow_ma_period=64, fast_ma_period=56, live=False):
    # todo don't forget to delete following in Colab
    slow_ma_period = 30
    fast_ma_period = 18

    df = pd.read_csv(constants.csv_file_path)
    median_volume, min_price = get_median_min(slow_ma_period=slow_ma_period, df=df)
    max_min_dic = get_max_min_price(df)
    strategy = (
        SmaCrossStrategy,
        dict(
            slow_ma_period=slow_ma_period,
            fast_ma_period=fast_ma_period,

            max_min_dic=max_min_dic,
            median_volume=median_volume,
            min_price=min_price,
            buying_power=800,
            loss_value=15,
            last_sale_price=None,
        ))

    result = BacktraderStrategy(live).add_strategy(strategy).run()
    logging.info(
        f"Number of Trades: {result.trading_count}\nerrors(buy,sell): {result.max_errors}")

    # logging.info(
    #     f"Number of Trades: {result.state.trading_count}\nReturn on investment: {round(result.state.total_return_on_investment * 100, 3)}%")


def get_median_min(slow_ma_period=None, df=None):
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

    close = df['close'].rolling(window=slow_ma_period).mean()  # get sma

    close = close[slow_ma_period - 1:]
    df = df[slow_ma_period - 1:]
    df.reset_index(drop=True, inplace=True)  # Reset the index of the new DataFrame if needed

    stop = get_stop_point(close)
    min_value = df['close'].iloc[:stop].min()
    median = df['volume'].median()
    logging.info(f'median ={median}--min_value={min_value}')
    return median, min_value


def get_max_min_price(df):
    # parse column as a datetime
    df['date'] = pd.to_datetime(df['timestamp'])
    # Extract just the date part from the datetime column
    df['date'] = df['date'].dt.date

    # Group by the date and calculate min and max for each group
    summary_df = df.groupby('date')['close'].agg(['max', 'min']).reset_index()

    # Convert the summary DataFrame to a dictionary
    summary_dict = {}
    for i, row in summary_df.iterrows():
        summary_dict[str(row['date'])] = (row['max'], row['min'])

    return summary_dict


def get_sma_cross_strategy_v2_optimum_params(max_min_dic=None, median_volume_min_price=None, slow_ma_period=None,
                                             fast_ma_period=None, start_count=None, stop_count=None):
    buy_error = 1000
    sell_error = 1000
    mean_error = 1000
    buying_power = 800
    loss_value = 15
    last_sale_price = None
    median_volume, min_price = median_volume_min_price

    count = 0
    best_count = 0
    statistics = {}

    header = ["iteration", "Trading Count", "Buy Error", "Sell Error", "Mean Error", "Fast Period", "Slow Period"]
    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # writing the header
    try:
        for pf in range(fast_ma_period, 300):
            for ps in range(slow_ma_period, 500):
                if pf > ps:
                    continue

                if stop_count > count >= start_count:

                    result = BacktraderStrategy(live=False
                                                ).add_strategy((SmaCrossStrategy,
                                                                dict(
                                                                    slow_ma_period=ps,
                                                                    fast_ma_period=pf,
                                                                    max_min_dic=max_min_dic,

                                                                    buying_power=buying_power,
                                                                    min_price=min_price,
                                                                    loss_value=loss_value,
                                                                    last_sale_price=last_sale_price,
                                                                    median_volume=median_volume, ))).run()
                    me = (result.max_errors[0] + result.max_errors[1]) / 2
                    statistics[me] = [count, result.trading_count, result.max_errors[0], result.max_errors[1], me, pf, ps]

                    if me < mean_error:
                        mean_error = me
                        buy_error = result.max_errors[0]
                        sell_error = result.max_errors[1]
                        best_count = count
                        print(
                            f"count : {count}\nBest errors(buy,sell): {round(buy_error, 3)},{round(sell_error, 3)}\nslow_ma_period={ps}\nfast_ma_period={pf}")
                    print(f'{count}-{best_count}:::{buy_error},{sell_error}')
                    # print(result.total_return_on_investment)
                    if count % 2000 == 0:
                        write_csv(statistics)
                elif count == stop_count:

                    print(f"Last Count: {count}")
                    print(f"Best errors(buy,sell): {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")

                    write_csv(statistics)

                    raise Exception("=== Parameter Tuning successfully terminated===")
                count += 1
        print(f"Total Count: {count}-Best errors(buy,sell): {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"current Count: {count}-Best errors(buy,sell): {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")
        write_csv(statistics)

    except:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"current Count: {count}-Best errors(buy,sell): {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")
        write_csv(statistics)


def write_csv(statistics):
    sorted_keys = sorted(statistics.keys())[:len(statistics)//2]
    with open(constants.stat_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        for key in sorted_keys:
            writer.writerow(statistics[key])  # writing each entry as a row

    statistics.clear()
    print('data written to csv')

def sma_cross_v2_config_process(config):
    return get_sma_cross_strategy_v2_optimum_params(**config)


def run_parallel(config_process=sma_cross_v2_config_process, configurations=None, start_count=0, increment=1000, processing_units = 2):
    processes = []
    if configurations is None:
        global config
        df = pd.read_csv(constants.csv_file_path)
        max_min = get_max_min_price(df)
        median_volume_min_price = get_median_min(slow_ma_period=config['slow_ma_period'], df=df)
        config['max_min_dic'] = max_min
        config['median_volume_min_price'] = median_volume_min_price
        for _ in range(processing_units):
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


config = dict(slow_ma_period=3, fast_ma_period=2)

if __name__ == "__main__":
    # import logger_config
    # run_single()
    run_parallel(start_count=0, increment=1300)
# run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
