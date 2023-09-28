import csv
import json
import logging
import os
import queue
import threading
from datetime import datetime, timedelta

import backtrader as bt
from alpaca.data import CryptoHistoricalDataClient, CryptoBarsRequest, TimeFrame
from websocket import WebSocketApp

from app.src import constants


class AlpacaCryptoHistoricalData:
    def __init__(self, symbol, period_in_days, csv_file_path):
        self.csv_file_path = csv_file_path
        self.symbol = symbol
        self.days = period_in_days
        self.client = CryptoHistoricalDataClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"))

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
        request_params = CryptoBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=t_frame,
            start=start_date.isoformat(),
            end=end_date.isoformat())

        return self.client.get_crypto_bars(request_params, feed='us').data

    def save_to_csv(self, data=None):
        bars = data or self.get_stock_historical_data()
        header = list(dict(bars[self.symbol][0]).keys())

        with open(self.csv_file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()

            for entry in bars[self.symbol]:
                writer.writerow(dict(entry))

        logging.info("Data has been written to '{}' file.".format(self.csv_file_path))


class Alpaca_Crypto_WebSocket:

    def __init__(self, key, secret, url, data_queue):
        self.ws = None
        self.thread = None
        self.key = key
        self.secret = secret
        self.url = url
        self.data_queue = data_queue

    def on_message(self, ws, message):
        # print(message)
        for d in json.loads(message):
            # print(f'data update:{d}')
            if d.get('T') == 'b':
                self.data_queue.put(d)

    def on_error(self, ws, error):
        logging.critical(f"Error occurred on live data stream: {error}")
        # news(f"Error occurred on alpaca live data stream: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.warning("live data stream closed")
        # news("live data stream closed")

    def on_open(self, ws):
        logging.info("live crypto data stream opened")
        auth_data = {
            "action": "auth",
            "key": self.key,
            "secret": self.secret
        }
        ws.send(json.dumps(auth_data))

        listen_message = {
            "action": "subscribe",
            "trades": ["LINK/USD"],
            "bars": ["LINK/USD"]
        }
        ws.send(json.dumps(listen_message))

    def start(self):
        def run_ws():
            self.ws = WebSocketApp(self.url,
                                   on_message=self.on_message,
                                   on_error=self.on_error,
                                   on_close=self.on_close,
                                   on_open=self.on_open)

            self.ws.run_forever()

        self.thread = threading.Thread(target=run_ws)
        self.thread.start()

    def stop(self):
        if self.ws:
            self.ws.close()
            self.thread.join()


class AlpacaCryptoStreamData(bt.feed.DataBase):

    def __init__(self, q=queue.Queue()):
        # super().__init__()
        self.ws = None
        self.data_queue = q

    def start(self):

        self.ws = Alpaca_Crypto_WebSocket(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"),
                                          constants.crypto_data_stream_wss, self.data_queue)
        self.ws.start()

    def stop(self):
        self.ws.stop()

    def _load(self):
        try:
            al_data = self.data_queue.get()  # get_nowait()
            # print("alpaca data =", al_data)
            self._map_bar(al_data)
        except queue.Empty:

            logging.warning("queue empty")
            return False
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt-the trading has been terminated")
            # voice_alert('say the trading has been terminated', 1)
            return False

        except Exception as e:
            logging.error(f"An error occurred from AlpacaStreamData: {e}")
            return False

        return True

    def _map_bar(self, data_dict):

        date_string = data_dict.get('t')
        if date_string and data_dict.get('T') == 'b':

            # Convert the string to a datetime object
            date = datetime_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00')).replace(tzinfo=None)

            self.lines.datetime[0] = bt.date2num(date)
            self.lines.close[0] = data_dict["c"]
            self.lines.low[0] = data_dict["l"]
            self.lines.high[0] = data_dict["h"]
            self.lines.open[0] = data_dict["o"]
            self.lines.volume[0] = data_dict["v"]
            # self.tick_data.append(f'{date_string_trimmed}, {data_dict["p"]}, {data_dict["p"]}, {data_dict["p"]}, {data_dict["p"]},{data_dict["p"]}')
            # do this before submit date = datetime.strptime(date_string_trimmed, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            date_string = data_dict.get('timestamp')
            if date_string:
                self.lines.datetime[0] = bt.date2num(date_string)
                self.lines.open[0] = data_dict['open']
                self.lines.high[0] = data_dict['high']
                self.lines.low[0] = data_dict['low']
                self.lines.close[0] = data_dict['close']
                self.lines.volume[0] = data_dict['volume']


# AlpacaCryptoHistoricalData("LINK/USD", 6, constants.crypto_file_path).save_to_csv()
# ws = Alpaca_Crypto_WebSocket(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"),
#                              constants.crypto_data_stream_wss, queue.Queue())
# ws.start()
