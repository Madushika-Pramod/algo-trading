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
        f"Number of Trades: {result.trading_count}\nerrors: {result.max_errors}")

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
    buying_power = 800
    loss_value = 15
    last_sale_price = None
    median_volume, min_price = median_volume_min_price

    count = 0
    best_count = 0
    # statistics = [["iteration", "Trading Count", "Roi", "Fast Period", "Slow Period", "devfactor"]]
    try:
        for pf in range(fast_ma_period, 31):
            for ps in range(slow_ma_period, 100):
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
                    # statistics.append(
                    #     [count, result.trading_count, result.average_return_on_investment, ps, p, e,
                    #      bgv, sgv])
                    if result.max_errors[0] < buy_error and result.max_errors[1] < sell_error:
                        buy_error = result.max_errors[0]
                        sell_error = result.max_errors[1]
                        best_count = count
                        print(
                            f"count : {count}\nBest errors: {round(buy_error, 3)},{round(sell_error, 3)}\nslow_ma_period={ps}\nfast_ma_period={pf}")
                    print(f'{count}-{best_count}--{buy_error},{sell_error}')
                    # print(result.total_return_on_investment)
                elif count == stop_count:

                    print(f"Last Count: {count}")
                    print(f"Best ROI: {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")
                    # write_csv(statistics)

                    raise Exception("=== Parameter Tuning successfully terminated===")
                count += 1
        print(f"Total Count: {count}-Best ROI: {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...save following data if you can't find tuned parameters")
        print(f"current Count: {count}-Best ROI: {round(buy_error, 3)},{round(sell_error, 3)} at count : {best_count}")
        # write_csv(statistics)


def write_csv(statistics):
    # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]

    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(header)  # writing the header

        for entry in statistics:
            writer.writerow(entry)  # writing each entry as a row


def sma_cross_v2_config_process(config):
    return get_sma_cross_strategy_v2_optimum_params(**config)


def run_parallel(config_process=sma_cross_v2_config_process, configurations=None, start_count=0, increment=1000):
    processes = []
    if configurations is None:
        global config
        df = pd.read_csv(constants.csv_file_path)
        max_min = get_max_min_price(df)
        median_volume_min_price = get_median_min(slow_ma_period=config['slow_ma_period'], df=df)
        config['max_min_dic'] = max_min
        config['median_volume_min_price'] = median_volume_min_price
        for _ in range(2):
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


config = dict(slow_ma_period=8, fast_ma_period=2)

if __name__ == "__main__":
    # import logger_config

    # run_single()
    run_parallel(start_count=0, increment=100)
# run_parallel(sma_cross_v2_config_process, configurations_for_sma_cross_v2)
