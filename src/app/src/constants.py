# from strategies import MovingAverageADXStrategy
import os

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

# Construct the full path to the data file

symbol = "AAPL"
time_frame = "minute"  # hour
period_in_days = 1
cash = 1000000
csv_file_path = os.path.join(parent_dir, 'datas', '{}.csv'.format(symbol))
data_download = 0
time_for_rate_limit = 3
market_data_url = "https://data.alpaca.markets/v2/stocks/"
# best_strategy = MovingAverageADXStrategy
