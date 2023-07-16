import queue

import constants
from .alpaca_data import AlpacaStreamData
from .backtrader import BacktraderStrategy, load_data


def _append_historical_data(q):
    df = load_data(constants.csv_file_path)
    for row in df.to_dict(orient='records'):
        # Insert each row (a Series) into the queue
        q.put(row)


class RealTimeTrader:
    def __init__(self, best_strategy=constants.best_strategy, q=None):
        self.best_strategy = best_strategy
        if q is None:
            q = queue.Queue()
        # _append_historical_data(q)
        self.data = AlpacaStreamData(q=q)

    def run(self):
        # self.data.start()
        backtrader_strategy = BacktraderStrategy(self.best_strategy, live=True)
        backtrader_strategy.cerebro.adddata(self.data)
        backtrader_strategy.cerebro.run(live=True)
