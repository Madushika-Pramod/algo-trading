# from strategies import MovingAverageADXStrategy
import os
from datetime import datetime

# Get the directory of the current file
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(os.path.dirname(_current_dir))

#variables ==>
pending_order = None
accepted_order = None
# <==

symbol = "GOOGL"
commission = 0.0  # 0.005
min_price = 128.8
median_volume = 500
file_id = datetime.now()
stat_file_path = os.path.join(_parent_dir, 'datas', f'stat{file_id}.csv')
# tick_file_path = os.path.join(_parent_dir, 'datas', f'tick{file_id}.csv')
voice_alert_frequency = 3

time_frame = "minute"  # hour
period_in_days = 10

# your strategy dynamically sizes positions based on available cash,
# it might attempt to different position when you change cash amount so
# adjust`AllInSizer._getsizing()`if you get an error, also fractional sizes not allowed in backtrader for current config
cash = 5000
csv_file_path = os.path.join(_parent_dir, 'datas', f'{symbol}{period_in_days}.csv')
# csv_file_path = os.path.join(_parent_dir, 'datas', 'data.csv')

data_download = 0
# time_for_rate_limit = 3
market_data_url = 'https://data.alpaca.markets/v2/stocks/'
trade_stream_wss = 'wss://paper-api.alpaca.markets/stream'
data_stream_wss = 'wss://stream.data.alpaca.markets/v2/iex'
# best_strategy = MovingAverageADXStrategy

