import json
import logging
import os
import queue
import re
import ssl
import threading
import time

import pandas as pd
import websocket

from app.src import constants
from app.src.notify import news
from broker.src.alpaca_data import AlpacaWebSocket


def extract_data(data):
    data_points = re.split(r'~m~\d+~m~', data)[1:]
    results = []
    pattern = r'((?<=NASDAQ:)\w+).*v":({.+\d})'

    for point in data_points:

        match = re.search(pattern, point)
        if match:
            symbol = match.group(1)
            json_ob = json.loads(match.group(2))

            results.append({
                "symbol": symbol,
                "volume": json_ob.get('volume'),
                "last_price": json_ob.get('lp'),
                "time": json_ob.get('lp_time'),
                "p_change": json_ob.get('ch'),
                "ch_percentage": json_ob.get('chp'),
                "extended_hours_price": json_ob.get('rtc'),
                "ehp_percentage": json_ob.get('rchp'),

            })

    # print(results)
    sorted_data = sorted(results, key=lambda x: x['time'])  # sort by time

    return sorted_data


def write_to_csv(df4, filename=constants.trading_view_file_path):
    # Check if the file already exists
    if not os.path.exists(filename):
        # Write the DataFrame to a CSV file
        df4.to_csv(filename, index=False)
        logging.info(f"Data written to {filename}")
    else:
        logging.info(f"File '{filename}' already exists. No data was written.")


def build_dataframe(lists):
    # Flatten the list of lists into a single list of dictionaries
    flattened_data = [item for sublist in lists for item in sublist]

    # Convert this flattened list into a pandas DataFrame
    df3 = pd.DataFrame(flattened_data,
                       columns=['symbol', 'volume', 'last_price', 'time', 'p_change', 'ch_percentage',
                                "extended_hours_price", "ehp_percentage"])

    # columns = ['symbol', 'volume', 'last_price', 'datetime', 'cumulative_change', 'cc_percentage',
    #            "extended_hours_price", "ehp_change"])
    # todo fill na
    # df3['last_price'].fillna(method='ffill', inplace=True)
    # df3['p_change'].fillna(method='ffill', inplace=True)
    # df3['ch_percentage'].fillna(method='ffill', inplace=True)
    # df3['symbol'].fillna(method='ffill', inplace=True)

    # Convert the 'datetime' column to integers
    # Attempt to convert the 'datetime' column to integers, setting errors='coerce' to turn failures into NaN
    df3['time'] = pd.to_numeric(df3['time'], errors='coerce').astype('Int64')

    # Calculate the forward and backward fill
    ffill = df3['time'].fillna(method='ffill')
    bfill = df3['time'].fillna(method='bfill')

    # Calculate the midpoint
    midpoint = (ffill + bfill) // 2  # Use // for integer division

    # Where the original 'time' column is NaN, replace with the midpoint
    df3['time'] = df3['time'].where(df3['time'].notna(), midpoint)
    df3['datetime'] = pd.to_datetime(df3['time'], unit='s')

    return df3


class TradingViewWebSocket:
    def __init__(self, data_queue):
        # self.restart_required = False

        self.thread = None
        self.ws = None
        self.headers = {
            'Connection': 'Upgrade',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Upgrade': 'websocket',
            'Sec-WebSocket-Version': '13',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Host': 'data.tradingview.com',
        }
        self.data_lists = []
        self.data_queue = data_queue

    def on_open(self, ws):
        print("TradingViewWebSocket opened")
        # ws.send('~m~36~m~{"m":"set_data_quality","p":["low"]}')
        ws.send('~m~52~m~{"m":"quote_create_session","p":["qs_2YiWuxHOASlh"]}')
        ws.send(
            '~m~474~m~{"m":"quote_set_fields","p":["qs_2YiWuxHOASlh","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","value_unit_id","rchp","rtc","country_code","provider_id"]}')
        if constants.symbol == "TSLA":
            ws.send('~m~63~m~{"m":"quote_add_symbols","p":["qs_2YiWuxHOASlh","NASDAQ:TSLA"]}')
        elif constants.symbol == "GOOGL":
            ws.send('~m~64~m~{"m":"quote_add_symbols","p":["qs_2YiWuxHOASlh","NASDAQ:GOOGL"]}')

    def on_message(self, ws: websocket, message):
        if message is None or message == "":
            return
        # print(f'msg{message}')
        pattern = r"^~m~\d+~m~~h~\d+"
        if re.match(pattern, message):
            ws.send(message)

        else:
            data = extract_data(message)
            if data is not None and len(data) > 0:
                self.data_lists.append(data)
                for d in data:
                    self.data_queue.put(d)
                    # print(d)

    def on_error(self, error, _):
        logging.error(f"At TradingViewWebSocket Process: {error}")
        news(f"Error occurred on trading view live data stream: {error}")
    def on_close(self, ws, status_code, msg):

        df2 = build_dataframe(self.data_lists)
        write_to_csv(df2)
        self.data_lists.clear()
        logging.info(f"TradingViewWebSocket Process closed: {status_code}:{msg}")
        # self.restart_required = True

        # self.ws2 = AlpacaWebSocket(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"),
        #                            constants.data_stream_wss, self.data_queue)
        # self.ws2.start()

    def stop(self):
        # self.restart_required = False
        df2 = build_dataframe(self.data_lists)
        write_to_csv(df2)
        self.data_lists.clear()
        if self.ws:
            self.ws.close()
            self.thread.join()

    def start(self):
        def run_ws():
            # while self.restart_required or not self.ws:
            self.ws = websocket.WebSocketApp(
                'wss://data.tradingview.com/socket.io/websocket',
                header=self.headers,
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error)

            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                # if self.restart_required:
                #     time.sleep(2)

        self.thread = threading.Thread(target=run_ws, daemon=True)
        self.thread.start()

# # Example of how to use the class
# if __name__ == "__main__":
# tv_ws = TradingViewWebSocket(queue.Queue())
# tv_ws.start()
# try:
#     tv_ws.thread.join()
# except KeyboardInterrupt:
#     print("Main loop interrupted. Cleaning up...")
#     tv_ws.stop()

# disable queue put