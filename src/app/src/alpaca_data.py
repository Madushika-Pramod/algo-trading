# import asyncio
# import csv
# import os
# import queue
# import threading
# from datetime import datetime, timedelta
#
# import backtrader as bt
# from alpaca.data.historical import StockHistoricalDataClient
# from alpaca.data.live import StockDataStream
# from alpaca.data.requests import StockBarsRequest
# from alpaca.data.timeframe import TimeFrame
# from backtrader import date2num
#
# import constants
#
#
# class AlpacaStreamData(bt.feed.DataBase):
#     params = (
#         ('q', queue.Queue()),
#     )
#
#     def __init__(self, rate_limit=constants.time_for_rate_limit,
#                  api_key=None, secret_key=None,
#                  symbol=constants.symbol):
#         self.thread = None
#         self.time_for_rate_limit = rate_limit
#         self.symbol = symbol
#         self.api_key = api_key or os.environ.get("API_KEY")
#         self.secret_key = secret_key or os.environ.get("SECRET_KEY")
#
#     def start(self):
#         self.thread = threading.Thread(target=self.run)
#         self.thread.start()
#
#     def _load(self):
#         try:
#
#             data = self.p.q.get(timeout=self.time_for_rate_limit)
#             data_dict = data.get('trade')
#             if data_dict:
#
#                 dt_str = data_dict.get('t')  # Using .get() will return None if 't' doesn't exist
#                 if dt_str:
#
#                     # dt_str = re.search(r'\d+-\d\d-\d\d.+\.\d{0,6}(?=[\dZ])', dt_str).group()
#                     parts = dt_str.split('.')
#                     dt_str = "{:.6f}".format(float("0." + parts[1][:-1])) + "+00:00"
#                     dt = datetime.fromisoformat(parts[0] + dt_str[1:])  # Convert string to datetime object
#                     float_timestamp = date2num(dt)
#                     # if float_timestamp is None:
#                     #     print("returned from 55")
#                     #     return True
#                     self.lines.datetime[0] = float_timestamp
#                 else:
#                     print("error at line 61 " + str(data_dict))
#                     return False
#
#                 self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = data_dict[
#                     "p"]
#
#                 self.lines.volume[0] = data_dict["s"]
#                 # time.sleep(self.time_for_rate_limit)
#                 self.p.q.task_done()
#                 print(dt)
#                 return True
#             data_open = data.get("open")
#             if data_open is None:
#                 return False
#             float_timestamp = date2num(data["timestamp"])
#             self.lines.datetime[0] = float_timestamp
#             self.lines.open[0] = data_open
#             self.lines.high[0] = data["high"]
#             self.lines.low[0] = data["low"]
#             self.lines.close[0] = data["close"]
#             self.lines.volume[0] = data["volume"]
#
#             self.p.q.task_done()
#             return True
#         except queue.Empty:
#             print("queue.Empty")
#             return False
#         except Exception as e:
#             print("An exception occurred in line 60:", str(e))
#             raise
#
#     def run(self):
#         # Connect to the Alpaca API and subscribe to the WebSocket stream
#         # Each message received should be put into self.p.q
#         wss_client = StockDataStream(self.api_key, self.secret_key)
#
#         async def bar_callback(bar):
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             print(bar)
#             loop.run_until_complete(self.p.q.put(bar))
#             loop.close()
#
#         # Subscribing to bar event
#         wss_client.subscribe_trades(bar_callback, self.symbol)
#
#         wss_client.run()
#
#
# class AlpacaHistoricalData:
#     def __init__(self, symbol, period_in_days, csv_file_path, api_key=None,
#                  secret_key=None):
#         self.csv_file_path = csv_file_path
#         self.symbol = symbol
#         self.days = period_in_days
#         self.client = StockHistoricalDataClient(api_key or os.environ.get("API_KEY"),
#                                                 secret_key or os.environ.get("SECRET_KEY"))
#
#     def get_stock_historical_data(self, period=constants.time_frame):
#         t_frame = None
#         if period == "hour":
#             t_frame = TimeFrame.Hour
#         elif period == "minute":
#             t_frame = TimeFrame.Minute
#
#         start_date = datetime.now() - timedelta(days=self.days)
#         #  Sri lanka is 5 hours and 30 minutes ahead of UTC + 15 min
#         # todo check this on none trading time
#         end_date = datetime.now() - timedelta(minutes=345)
#         request_params = StockBarsRequest(
#             symbol_or_symbols=self.symbol,
#             timeframe=t_frame,
#             start=start_date.isoformat(),
#             end=end_date.isoformat())
#
#         return self.client.get_stock_bars(request_params).data
#
#     def save_to_csv(self):
#         bars = self.get_stock_historical_data()
#         header = list(dict(bars[self.symbol][0]).keys())
#
#         with open(self.csv_file_path, 'w', newline='') as file:
#             writer = csv.DictWriter(file, fieldnames=header)
#             writer.writeheader()
#
#             for entry in bars[self.symbol]:
#                 writer.writerow(dict(entry))
#
#         print("Data has been written to '{}' file.".format(self.csv_file_path))
