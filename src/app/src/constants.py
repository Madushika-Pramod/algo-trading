# from strategies import MovingAverageADXStrategy
import os
from datetime import datetime

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

# Construct the full path to the data file

symbol = "GOOGL"
commission = 0.005
min_price = 129.53
average_volume = 39_406
stat_id = datetime.now()
stat_file_path = os.path.join(parent_dir, 'datas', f'stat{stat_id}.csv')

time_frame = "minute"  # hour
period_in_days = 10

# your strategy dynamically sizes positions based on available cash,
# it might attempt to different position when you change cash amount so
# adjust`AllInSizer._getsizing()`if you get an error, also fractional sizes not allowed in backtrader for current config
cash = 5_00
csv_file_path = os.path.join(parent_dir, 'datas', f'{symbol}{period_in_days}.csv')
# csv_file_path = os.path.join(parent_dir, 'datas', 'dummy_stock_data.csv')

data_download = 0
time_for_rate_limit = 3
market_data_url = "https://data.alpaca.markets/v2/stocks/"
# best_strategy = MovingAverageADXStrategy
