import multiprocessing

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


def get_trend_line_strategy_optimum_params(best_roi=0.0, period=3, degree=3, slow=4, fast=3, predicted_line_length=2,
                                           line_degree=1, b_band_period=2):
    for d in range(degree, 4):
        print(f"degree :{d}")
        for p in range(period, 31):
            if p == 3: break
            if p > d:
                print(p)
                for ld in range(line_degree, 3):
                    for ll in range(predicted_line_length, 11, 2):
                        for bp in range(b_band_period, 41):
                            for f in range(fast, 11):
                                print(f"fast ma: {f}")
                                for s in range(slow, 41):
                                    print(f"slow ma: {s}")

                                    if f < s:
                                        for df in range(2, 7):
                                            df /= 2
                                            score = BacktraderStrategy(
                                            ).add_strategy((TrendLineStrategy,
                                                            dict(period=p, poly_degree=d, fast=f, slow=s,
                                                                 predicted_line_length=ll,
                                                                 line_degree=ld, devfactor=df, b_band_period=bp))).run()
                                            if score > best_roi:
                                                best_roi = score
                                                print(
                                                    f"Best ROI: {best_roi:.2f}\nPeriod: {p}\nDegree: {d}\nSlow: {s}\nFast: {f}\nLine Length: {ll}\nLine Degree: {ld}\nDev Factor: {df}\n Bollinger Period: {bp}")


def config_process_1():
    return get_trend_line_strategy_optimum_params(best_roi=0.0, period=2, degree=1, slow=1, fast=1,
                                                  predicted_line_length=2,
                                                  line_degree=1, b_band_period=2)


# for period =3 slow ma = 15 fast = 1


def config_process_2():
    return get_sma_cross_strategy_optimum_params(best_roi=0.033, slow=4, fast=3)


def run_parallel():
    # Create processes
    p1 = multiprocessing.Process(target=config_process_1)
    p2 = multiprocessing.Process(target=config_process_2)

    # Start processes
    p1.start()
    p2.start()

    # Wait for both processes to finish
    p1.join()
    p2.join()

    print('Both functions have finished executing')


if __name__ == "__main__":
    config_process_1()
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
