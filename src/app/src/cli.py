import multiprocessing
import threading
import time

from app.src.back_trader import BacktraderStrategy
from strategies import SmaCrossStrategy
from strategies import TrendLineStrategy


# from .back_trader import BacktraderStrategy

def run_single():
    strategy = (
        TrendLineStrategy,
        dict(period=20, fast=1, slow=20, poly_degree=3, predicted_line_length=2, line_degree=1, devfactor=1.0))
    score = BacktraderStrategy().add_strategy(strategy).run()
    print(score)


def run_multi():
    strategies = [
        (TrendLineStrategy,
         dict(period=10, poly_degree=2, fast=3, slow=10, predicted_line_length=2, line_degree=1, devfactor=1.0)),
        (SmaCrossStrategy, dict(pfast=10, pslow=30))]
    for strategy in strategies:
        score = BacktraderStrategy().add_strategy(strategy).run()
        print(score)


def get_sma_cross_strategy_optimum_params(best_roi=0.033, slow=4, fast=3, ):
    for f in range(fast, 41):
        print(f"sma cross fast: {f}")
        for s in range(slow, 10):
            if f < s:
                score = BacktraderStrategy().add_strategy((SmaCrossStrategy, dict(pfast=f, pslow=s))).run()
                if score > best_roi:
                    best_roi = score

                    print(f"Best ROI: {best_roi}\nSlow: {s}\nFast: {f}")


def get_trend_line_strategy_optimum_params(best_roi=0.0, period=2, curve_degree=3, slow=4, fast=3,
                                           predicted_line_length=2,
                                           line_degree=1, b_band_period=2):
    count = 0

    best_roi2 = 0
    period2 = 0
    curve_degree2 = 0
    slow2 = 0
    fast2 = 0
    predicted_line_length2 = 0
    line_degree2 = 0
    b_band_period2 = 0
    deviation_factor = 0
    try:

        for bp in range(b_band_period, 41):
            if bp == b_band_period + 1:
                # print(
                #     f"Last Period: {p-1}===Degree: {d}\n Elapsed time: {(time.time() - start_time) / 60} minutes")
                print(bp - 1, threading.get_ident())
                print(f"Total Count: {count}")
                raise Exception("===xxxxxx===")
            for s in range(slow, 41):
                for f in range(fast, 21):
                    for p in range(period, 31):
                        for d in range(curve_degree, 4):

                            # print(f"degree :{d}")
                            # range(period, 31)
                            # if p == 3: break
                            # print(p)
                            for ld in range(line_degree, 3):

                                # print(f"{p}line_degree{ld}")
                                for ll in range(predicted_line_length, 11, 2):
                                    # print(f"{ld}predicted_line_length{ll}")

                                    if f < s and p > d > ld and p > ll > ld:
                                        # print(f"slow ma: {s}", end="_")

                                        for df in range(2, 5):
                                            # Dev-Factor from 1, 1.5, 2
                                            df /= 2
                                            # start_time = time.time()
                                            # score = BacktraderStrategy(
                                            # ).add_strategy((TrendLineStrategy,
                                            #                 dict(period=p, poly_degree=d, fast=f, slow=s,
                                            #                      predicted_line_length=ll,
                                            #                      line_degree=ld, devfactor=df,
                                            #                      b_band_period=bp))).run()

                                        count += 1
                                        # print(count)
                                        # print(f"time diff ={time.time()-start_time}")

                                        period2 = p
                                        curve_degree2 = d
                                        slow2 = s
                                        fast2 = f
                                        predicted_line_length2 = ll
                                        line_degree2 = ld
                                        b_band_period2 = bp
                                        deviation_factor = df
                                        # if score > best_roi:
                                        #     best_roi2 = best_roi = score
                                        #     print(
                                        #         f"Best ROI: {best_roi:.2f}\nPeriod: {p}\nDegree: {d}\nSlow: {s}\nFast: {f}\nLine Length: {ll}\nLine Degree: {ld}\nDev Factor: {df}\n Bollinger Period: {bp}")
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Performing cleanup...")
        print(
            f"Best ROI: {best_roi2:.2f}\nPeriod: {period2}\nDegree: {curve_degree2}\nSlow: {slow2}\nFast: {fast2}\nLine Length: {predicted_line_length2}\nLine Degree: {line_degree2}\nDev Factor: {deviation_factor}\n Bollinger Period: {b_band_period2}")


def config_process_1():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=1)


# for period 5 slow ma = 15 fast = 1


def config_process_2():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=2)


# return get_sma_cross_strategy_optimum_params(best_roi=0.033, slow=2, fast=3)
def config_process_3():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=3)


def config_process_4():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=4)


def config_process_5():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=5)


def config_process_6():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=6)


def config_process_7():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=7)


def config_process_8():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=5, curve_degree=2, slow=2, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=8)




def run_parallel():
    # Create processes
    p1 = multiprocessing.Process(target=config_process_1)
    p2 = multiprocessing.Process(target=config_process_2)
    p3 = multiprocessing.Process(target=config_process_3)
    p4 = multiprocessing.Process(target=config_process_4)
    # p5 = multiprocessing.Process(target=config_process_5)
    # p6 = multiprocessing.Process(target=config_process_6)
    # p7 = multiprocessing.Process(target=config_process_7)
    # p8 = multiprocessing.Process(target=config_process_8)

    # Start processes
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    # p5.start()
    # p6.start()
    # p7.start()
    # p8.start()

    # Wait for both processes to finish
    p1.join()
    p2.join()
    p3.join()
    p4.join()
    # p5.join()
    # p6.join()
    # p7.join()
    # p8.join()

    print('Both functions have finished executing')


if __name__ == "__main__":
    run_parallel()
    # get_trend_line_strategy_optimum_params()

    # import csv
    # import plotly.graph_objects as go
    # import os
    # from app.src.constants import parent_dir
    #
    # # Read CSV file
    # # csv_file_path = os.path.join(parent_dir, 'datas', 'slopes.csv')
    # # with open(csv_file_path, 'r') as file:
    # #     reader_1 = csv.reader(file)
    # #     data_1 = list(reader_1)
    #
    # # Get 3rd column as y and column number as x
    # # x = list(range(len(data_1)))  # column numbers
    # #
    # # y = [float(row[2]) for row in data_1 if
    # #      (float(row[1]) > 0 and float(row[1]) > float(row[2]) or (float(row[1]) < 0 and float(row[1]) < float(row[2])))]
    # # third column data
    #
    # csv_file_path = os.path.join(parent_dir, 'datas', 'SPA.csv')
    # with open(csv_file_path, 'r') as file:
    #     reader_2 = csv.reader(file)
    #     data_2 = list(reader_2)
    #
    # x2 = list(range(len(data_2)))  # column numbers
    #
    # y2 = [float(data_2[i][5]) for i in range(1, len(data_2))]
    #
    # line_trace_price = go.Scatter(
    #     x=x2,
    #     y=y2,
    #     mode='lines',
    #     name='Price line'
    # )
    #
    # # Create a scatter trace with markers
    # scatter_market = go.Scatter(
    #     x=x2,
    #     y=y2,
    #     mode='markers',
    #     name='Markers'
    # )
    #
    # # Create a line trace
    # # line_trace = go.Scatter(
    # #     x=x,
    # #     y=y,
    # #     mode='lines',
    # #     name='Line'
    # # )
    #
    # # Create the figure and add the traces
    # fig = go.Figure(data=[line_trace_price, scatter_market])
    # # Create plot
    # # fig = go.Figure(data=go.Scatter(x=x, y=y, mode='markers',name='Markers'))
    #
    # # Show plot
    # fig.show()
