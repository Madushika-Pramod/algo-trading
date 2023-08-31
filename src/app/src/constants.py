# from strategies import MovingAverageADXStrategy
import os
from datetime import datetime

# variables ==>
# trading_view_data = {}
trading_view_data = dict(volume=-1000, last_price=-1000, lp_time=-1000, cumulative_change=-1000, cc_percentage=-1000,
                         extended_hours_price=-1000, ehp_percentage=-1000, close=-1000, open=-1000, high=-1000,
                         low=-1000)

pending_order = None
accepted_order = None
market_buy_order = False
# <==

symbol = "TSLA"
commission = 0.0  # 0.005
min_price = 254.69
median_volume = 4782.0  #14350.0
last_sale_price = None
cash = 500

voice_alert_frequency = 3

time_frame = "minute"  # hour
period_in_days = 10

# your strategy dynamically sizes positions based on available cash,
# it might attempt to different position when you change cash amount so
# adjust`AllInSizer._getsizing()`if you get an error, also fractional sizes not allowed in backtrader for current config


# Get the directory of the current file
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(os.path.dirname(_current_dir))
file_id = datetime.now()
stat_file_path = os.path.join(_parent_dir, 'datas', f'stat{file_id}.csv')
# tick_file_path = os.path.join(_parent_dir, 'datas', f'tick{file_id}.csv')
csv_file_path = os.path.join(_parent_dir, 'datas', f'{symbol}{period_in_days}.csv')
# csv_file_path = os.path.join(_parent_dir, 'datas', 'data.csv')
tick_file_path = os.path.join(_parent_dir, 'datas', 'tick.csv')
trading_view_file_path = os.path.join(_parent_dir, 'datas', f'tw_{symbol}{period_in_days}{file_id}.csv')

mama_file_path = os.path.join(_parent_dir, 'datas', f'MAMA{file_id}.csv')

data_download = 0
# time_for_rate_limit = 3
market_data_url = 'https://data.alpaca.markets/v2/stocks/'
trade_stream_wss = 'wss://paper-api.alpaca.markets/stream'
data_stream_wss = 'wss://stream.data.alpaca.markets/v2/iex'
# best_strategy = MovingAverageADXStrategy
