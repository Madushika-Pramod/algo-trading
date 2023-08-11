import csv
import multiprocessing
import os

from app.src import constants
from app.src.back_trader import BacktraderStrategy
from strategies import BollingerRSIStrategy, TrendLineStrategy, SmaCrossStrategy


def run_single(live=False):
    strategy = (
        SmaCrossStrategy,
        dict(
            fast_ma_period=10,
            slow_ma_period=34,
            high_low_period=15,
            high_low_tolerance=0.3,
            profit_threshold=2.5
        ))

    # strategy = (DemoStrategy, {})
    result = BacktraderStrategy(live).add_strategy(strategy).run()
    print(
        f"Number of Trades: {result.trading_count}\nReturn on investment: {round(result.total_return_on_investment * 100, 2)}%")


def run_multi():
    strategies = [
        (TrendLineStrategy,
         dict(period=10, poly_degree=2, predicted_line_length=2, line_degree=1, devfactor=1.0)),
        (SmaCrossStrategy, dict(pfast=10, pslow=30))]
    for strategy in strategies:
        score = BacktraderStrategy(live=False).add_strategy(strategy).run()
        print(score)


def get_sma_cross_strategy_optimum_params(best_roi=0, fast_ma_period=None, slow_ma_period=None, high_low_period=None,
                                          high_low_tolerance=None,
                                          profit_threshold=None):
    p2 = None
    count = 0
    roi_count = 0
    statistics = [
        ["iteration", "Trading Count", "Roi", "Fast Period", "Slow Period", "high & low Period", "high & low Error",
         "Gain Value"]]
    try:
        for p in range(high_low_period, 30):
            p2 = p
            if p == high_low_period + 1:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(p - 1)
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                write_csv(statistics)
                for x in range(10):
                    os.system('afplay /System/Library/Sounds/Ping.aiff')

                raise Exception("===xxxxxx===")
            for pf in range(fast_ma_period, 31):
                for ps in range(slow_ma_period, 61):
                    if pf > ps:
                        continue
                    for x in range(high_low_tolerance, 10):
                        # Dev-Factor from 1, 1.5, 2
                        e = x / 10
                        for y in range(profit_threshold, 9):
                            gv = y / 2
                            # if count > 8600:

                            # result = BacktraderStrategy(live=False
                            #                             ).add_strategy((SmaCrossStrategy,
                            #                                             dict(fast_ma_period=pf, slow_ma_period=ps,
                            #                                                  high_low_period=p,
                            #                                                  high_low_tolerance=e,
                            #                                                  profit_threshold=gv))).run()
                            # statistics.append(
                            #     [count, result.trading_count, result.total_return_on_investment, pf, ps, p, e, gv])
                            # if result.total_return_on_investment > best_roi:
                            #     best_roi = result.total_return_on_investment
                            #     roi_count = count
                            #     print(
                            #         f"count : {count}\nBest ROI: {best_roi * 100}%\nPeriod fast:{pf}\n Period Slow: {ps}\n high_low_period: {p}\n high_low_error: {e}\nGain value: {gv}")
                            # print(count)
                            count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...")
        print(f"high_low_period: {p2}-Total Count: {count}-Best ROI: {best_roi * 100}%")
        write_csv(statistics)


configurations_for_sma_cross = [
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=14, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=12, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=16, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=10, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=18, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=20, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=8, high_low_tolerance=2, profit_threshold=2),
    dict(fast_ma_period=2, slow_ma_period=3, high_low_period=22, high_low_tolerance=2, profit_threshold=2)

]


def get_bollinger_rsi_strategy_optimum_params(best_roi=0.0, bbperiod=13, rsiperiod=14, rsi_low=30, rsi_high=70,
                                              gain_value=0):
    # todo use dev factor as 1.5 remove loop
    # give more space to rsi and bollinger

    if rsi_low > 50 or rsi_high < 50:
        return
    bp2 = None
    count = 0
    roi_count = 0
    statistics = []
    try:
        for bp in range(bbperiod, 30):
            bp2 = bp
            if bp == bbperiod + 1:
                print(bp - 1)
                print(f"Total Count: {count}")
                print(f"Best ROI: {best_roi * 100}% at count : {roi_count}")
                write_csv(statistics)
                for x in range(10):
                    os.system('afplay /System/Library/Sounds/Ping.aiff')

                raise Exception("===xxxxxx===")
            for rp in range(rsiperiod, 46):  # typically it's between 5 and 30
                for rl in range(rsi_low, 46):  # range of 0-50
                    for rh in range(rsi_high, 61):  # 50-100
                        for x in range(3, 4):
                            # Dev-Factor from 1, 1.5, 2
                            df = x / 2
                            for y in range(gain_value, 4):
                                # gv = y / 2
                                # if count > count_continue:

                                score = BacktraderStrategy(
                                ).add_strategy((BollingerRSIStrategy,
                                                dict(bbperiod=bp, bbdev=df, rsiperiod=rp, rsi_low=rl, rsi_high=rh,
                                                     gain_value=y))).run()
                                statistics.append([score, df, rp, rl, rh, bp, y])
                                if score > best_roi:
                                    best_roi = score
                                    roi_count = count
                                    print(
                                        f"Best ROI: {best_roi * 100}%\nDev-Factor:{df}\n Rsi period: {rp}\n Rsi low: {rl}\n Rsi high: {rh}\n Bollinger Period: {bp}\n Gain value: {y}")
                                print(count)
                                count += 1

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...")
        print(f"Bollinger Period: {bp2}-Total Count: {count}-Best ROI: {best_roi * 100}%")
        write_csv(statistics)


def write_csv(statistics):
    # header = ["ROI", "Dev Factor", "Rsi period", "Rsi low", "Rsi high", "Bollinger Period", "Gain value"]

    with open(constants.stat_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(header)  # writing the header

        for entry in statistics:
            writer.writerow(entry)  # writing each entry as a row


configurations_for_bollinger = [
    # dict(bbperiod=5, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=6954),
    dict(bbperiod=7, rsiperiod=33, rsi_low=40, rsi_high=60, gain_value=3, count_continue=7029),
    # dict(bbperiod=9, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=6952),
    # dict(bbperiod=11, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=7004),
    # dict(bbperiod=13, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=6983),
    # dict(bbperiod=15, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=6927),
    # dict(bbperiod=17, rsiperiod=33, rsi_low=30, rsi_high=55, gain_value=3, count_continue=7020),
    # dict(bbperiod=19, rsiperiod=5, rsi_low=0, rsi_high=55, gain_value=5)
]


def get_trend_line_strategy_optimum_params(best_roi=-1.0, period=2, curve_degree=3,
                                           predicted_line_length=2,
                                           line_degree=1, b_band_period=2):
    count = 0

    best_roi2 = 0
    period2 = 0
    curve_degree2 = 0
    predicted_line_length2 = 0
    line_degree2 = 0
    b_band_period2 = 0
    deviation_factor = 0
    df = 0

    try:

        for bp in range(b_band_period, 41):
            if bp == b_band_period + 1:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(bp - 1)
                print(f"Total Count: {count}")
                print(
                    f"Best ROI: {best_roi}\nPeriod: {period2}\nDegree: {curve_degree2}\nLine Length: {predicted_line_length2}\nLine Degree: {line_degree2}\nDev Factor: {deviation_factor}\n Bollinger Period: {b_band_period2}")
                for x in range(10):
                    os.system('say "task completed"')
                raise Exception("===xxxxxx===")

            for p in range(period, 51):
                for d in range(curve_degree, 4):

                    for ld in range(line_degree, 3):
                        # line_degree max 2

                        # print(f"{p}line_degree{ld}")
                        for ll in range(predicted_line_length, 11, 2):
                            # print(f"{ld}predicted_line_length{ll}")

                            if p > d > ld and p > ll > ld:
                                # print(f"slow ma: {s}", end="_")

                                for x in range(2, 5):
                                    # Dev-Factor from 1, 1.5, 2
                                    df = x / 2
                                    score = BacktraderStrategy(
                                    ).add_strategy((TrendLineStrategy,
                                                    dict(period=p, poly_degree=d,
                                                         predicted_line_length=ll,
                                                         line_degree=ld, devfactor=df,
                                                         b_band_period=bp))).run()
                                    if score > best_roi:
                                        best_roi2 = best_roi = score
                                        print(
                                            f"Best ROI: {best_roi2}\nPeriod: {period2}\nDegree: {curve_degree2}\nLine Length: {predicted_line_length2}\nLine Degree: {line_degree2}\nDev Factor: {deviation_factor}\n Bollinger Period: {b_band_period2}")

                            count += 1
                            print(count)
                            period2 = p
                            curve_degree2 = d
                            predicted_line_length2 = ll
                            line_degree2 = ld
                            b_band_period2 = bp
                            deviation_factor = df

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...")
        print(
            f"Best ROI: {best_roi2}\nPeriod: {period2}\nDegree: {curve_degree2}\nLine Length: {predicted_line_length2}\nLine Degree: {line_degree2}\nDev Factor: {deviation_factor}\n Bollinger Period: {b_band_period2}")


configurations_for_trend_line = [
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 10},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 11},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 12},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 13},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 14},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 15},
    {"best_roi": -1.0, "period": 5, "curve_degree": 2, "predicted_line_length": 2, "line_degree": 1,
     "b_band_period": 16},
]


def sma_cross_config_process(config):
    return get_sma_cross_strategy_optimum_params(**config)


def trend_line_config_process(config):
    return get_trend_line_strategy_optimum_params(**config)


def bollinger_config_process(config):
    return get_bollinger_rsi_strategy_optimum_params(**config)


def run_parallel(config_process, configurations):
    # Create processes
    processes = [multiprocessing.Process(target=config_process, args=(config,)) for config in configurations]

    # Start processes
    for p in processes:
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    print('All functions have finished executing')


if __name__ == "__main__":
    run_single()
    # run_parallel(bollinger_config_process, configurations_for_bollinger)
    # run_parallel(sma_cross_config_process, configurations_for_sma_cross)
