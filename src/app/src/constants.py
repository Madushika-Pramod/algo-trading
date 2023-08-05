# from strategies import MovingAverageADXStrategy
import os
from datetime import datetime

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

# Construct the full path to the data file

symbol = "AAPL"
min_price = 182.85
average_appl2 = 63_881 / 2
stat_id = datetime.now()
stat_file_path = os.path.join(parent_dir, 'datas', f'stat{stat_id}.csv')

time_frame = "minute"  # hour
period_in_days = 1
cash = 5_000
csv_file_path = os.path.join(parent_dir, 'datas', f'{symbol}{period_in_days}.csv')
data_download = 0
time_for_rate_limit = 3
market_data_url = "https://data.alpaca.markets/v2/stocks/"
# best_strategy = MovingAverageADXStrategy
