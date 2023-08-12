import csv
import json
import os
import queue
import threading
from datetime import datetime, timedelta

import backtrader as bt
import requests
from alpaca.data import StockHistoricalDataClient, StockBarsRequest, TimeFrame
from websocket import WebSocketApp

from app.src import constants


class AlpacaWebSocket:

    def __init__(self, key, secret, url, data_queue):
        self.ws = None
        self.thread = None
        self.key = key
        self.secret = secret
        self.url = url
        self.data_queue = data_queue

    def on_message(self, ws, message):
        for d in json.loads(message):
            # print(d)
            if d.get('T') == 't':
                self.data_queue.put(d)


    def on_error(self, ws, error):
        print(f"Error occurred on live data stream: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("live data stream closed")

    def on_open(self, ws):
        print("live data stream opened")
        auth_data = {
            "action": "auth",
            "key": self.key,
            "secret": self.secret
        }
        ws.send(json.dumps(auth_data))

        listen_message = {
            "action": "subscribe",
            "trades": [constants.symbol]
        }
        ws.send(json.dumps(listen_message))

    def start(self):
        def run_ws():
            self.ws = WebSocketApp(self.url,
                                   on_message=self.on_message,
                                   on_error=self.on_error,
                                   on_close=self.on_close)
            self.ws.on_open = self.on_open
            self.ws.run_forever()

        self.thread = threading.Thread(target=run_ws)
        self.thread.start()

    def stop(self):
        if self.ws:
            self.ws.close()
            self.thread.join()


class AlpacaStreamData(bt.feed.DataBase):

    def __init__(self, q=queue.Queue()):
        super().__init__()
        self.ws = None
        self.data_queue = q

    def start(self):
        self.ws = AlpacaWebSocket(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"),
                                  constants.data_stream_wss, self.data_queue)
        self.ws.start()

    def stop(self):
        self.ws.stop()

    def _load(self):
        try:
            al_data = self.data_queue.get(timeout=120)  # get_nowait()
            # print("alpaca data =", al_data)
            self._map_bar(al_data)
        except queue.Empty:
            from app.src.voice_alert import voice_alert
            voice_alert('say the queue is empty')
            print("queue empty")
            return False
        except Exception as e:
            print("An error occurred: ", e)

        return True

    def _map_bar(self, data_dict):

        date_string = data_dict.get('t')
        if date_string and data_dict.get('T') == 't':

            # Trim the string to remove nanoseconds and trailing 'Z'
            date_string_trimmed = date_string[:23]

            # Convert the string to a datetime object
            date = datetime.strptime(date_string_trimmed, '%Y-%m-%dT%H:%M:%S.%f')
            self.lines.datetime[0] = bt.date2num(date)
            self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = data_dict["p"]
            self.lines.volume[0] = data_dict["s"]
            # todo add line.volumes to A LIST
        else:
            date_string = data_dict.get('timestamp')
            if date_string:
                self.lines.datetime[0] = bt.date2num(date_string)
                self.lines.open[0] = data_dict['open']
                self.lines.high[0] = data_dict['high']
                self.lines.low[0] = data_dict['low']
                self.lines.close[0] = data_dict['close']
                self.lines.volume[0] = data_dict['volume']


class AlpacaHistoricalData:
    def __init__(self, symbol, period_in_days, csv_file_path):
        self.csv_file_path = csv_file_path
        self.symbol = symbol
        self.days = period_in_days
        self.client = StockHistoricalDataClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"))

    def get_stock_historical_data(self, period=constants.time_frame):
        t_frame = TimeFrame.Minute
        # if period == "hour":
        #     t_frame = TimeFrame.Hour
        # elif period == "minute":
        #     t_frame = TimeFrame.Minute

        start_date = datetime.now() - timedelta(days=self.days)
        #  Sri lanka is 5 hours and 30 minutes ahead of UTC + 15 min
        # todo check this on none trading time
        end_date = datetime.now() - timedelta(minutes=345)
        request_params = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=t_frame,
            start=start_date.isoformat(),
            end=end_date.isoformat())

        return self.client.get_stock_bars(request_params).data

    def save_to_csv(self):
        bars = self.get_stock_historical_data()
        header = list(dict(bars[self.symbol][0]).keys())

        with open(self.csv_file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()

            for entry in bars[self.symbol]:
                writer.writerow(dict(entry))

        print("Data has been written to '{}' file.".format(self.csv_file_path))


class AlpacaHistoricalDataApi:
    def __init__(self, symbol, period_in_days, csv_file_path):
        self.csv_file_path = csv_file_path
        self.symbol = symbol
        self.days = period_in_days
        self.url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={self.symbol}&timeframe=1T"

        self.headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": f'{os.environ.get("API_KEY")}',
            "APCA-API-SECRET-KEY": f'{os.environ.get("SECRET_KEY")}'
        }

    def _get_stock_historical_data(self):

        def request_data(token=None):
            if token is not None:
                return requests.get(self.url + f"&page_token={token}", headers=self.headers)
            return requests.get(self.url, headers=self.headers)

        json_list = []

        start_date = datetime.now() - timedelta(days=self.days)
        #  Sri lanka is 5 hours and 30 minutes ahead of UTC + 15 min
        # todo check this on none trading time
        end_date = datetime.now() - timedelta(minutes=345)

        self.url += f"&start={start_date.isoformat()}Z&end={end_date.isoformat()}Z"
        response = request_data()

        json_list.append(response.json())
        while response.json()['next_page_token'] is not None:
            response = request_data(token=response.json()['next_page_token'])
            json_list.append(response.json())
        return json_list

    def save_to_csv(self):
        bars = self._get_stock_historical_data()

        fieldnames = list(dict(bars[0]['bars'][self.symbol][0]).keys())
        header = ["timestamp", "open", "high", "low", "close", "volume", "trade count", "vwap"]

        with open(self.csv_file_path, 'w', newline='') as file:
            csv.writer(file).writerow(header)
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            for bar in bars:
                for entry in bar['bars'][self.symbol]:
                    writer.writerow(dict(entry))

        print(f"Data has been written to '{self.csv_file_path}' file.")

# AlpacaHistoricalData(constants.symbol, constants.period_in_days, constants.csv_file_path).save_to_csv()
