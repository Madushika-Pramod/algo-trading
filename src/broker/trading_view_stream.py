import re
import ssl
import threading

import pandas as pd
import websocket


def extract_data(data):
    data_points = re.split(r'~m~\d+~m~', data)[1:]
    results = []

    for point in data_points:

        data_points = re.split(r'~m~\d+~m~', point)

        for point in data_points:
            match = re.search(
                r'"n":"NASDAQ:GOOGL".*?"volume":(\d+)(?:.*?"lp_time":(\d+))?(?:.*?"lp":([\d.]+))?(?:.*?"chp":([\d.]+))?(?:.*?"ch":([\d.]+))?(?:.*?"rtc":([\d.-]+))?(?:.*?"rchp":([\d.-]+))?',
                point)

            if match:
                volume = match.group(1)
                lp_time = match.group(2)
                lp = match.group(3)
                chp = match.group(4)
                ch = match.group(5)
                rtc = match.group(6)
                rchp = match.group(7)

            results.append({
                "symbol": "GOOGL",
                "volume": volume,
                "last_price": lp,
                "datetime": lp_time,
                "cumulative_change": ch,
                "cc_percentage": chp,
                "extended_hours_price": rtc,
                "ehp_change": rchp

            })
    print(results)
    return results


def write_to_csv(df4, filename='trading_view_output5.csv'):
    # Write the DataFrame to a CSV file
    df4.to_csv(filename, index=False)

    print(f"Data written to {filename}")


def build_dataframe(lists):
    # Flatten the list of lists into a single list of dictionaries
    flattened_data = [item for sublist in lists for item in sublist]

    # Convert this flattened list into a pandas DataFrame

    df3 = pd.DataFrame(flattened_data,
                       columns=['symbol', 'volume', 'last_price', 'datetime', 'cumulative_change', 'cc_percentage', "extended_hours_price", "ehp_change"])
    df3['last_price'].fillna(method='ffill', inplace=True)
    df3['cumulative_change'].fillna(method='ffill', inplace=True)
    df3['cc_percentage'].fillna(method='ffill', inplace=True)

    # Calculate the forward and backward fill
    ffill = df3['datetime'].fillna(method='ffill')
    bfill = df3['datetime'].fillna(method='bfill')

    # Calculate the midpoint
    midpoint = (ffill + bfill) / 2

    # Where the original 'datetime' column is NaN, replace with the midpoint
    df3['datetime'] = df3['datetime'].where(df3['datetime'].notna(), midpoint)

    return df3


class TradingViewWebSocket:
    def __init__(self, data_queue):
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
        print("Websocket opened")
        # ws.send('~m~36~m~{"m":"set_data_quality","p":["low"]}')
        ws.send('~m~52~m~{"m":"quote_create_session","p":["qs_2YiWuxHOASlh"]}')
        ws.send(
            '~m~474~m~{"m":"quote_set_fields","p":["qs_2YiWuxHOASlh","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","value_unit_id","rchp","rtc","country_code","provider_id"]}')
        ws.send('~m~64~m~{"m":"quote_add_symbols","p":["qs_2YiWuxHOASlh","NASDAQ:GOOGL"]}')

    def on_message(self, ws: websocket, message):
        pattern = r"^~m~\d+~m~~h~\d+"
        if re.match(pattern, message):
            ws.send(message)

        else:
            d = extract_data(message)
            self.data_lists.append(d)
            self.data_queue.put(d)

    def on_error(self, error):
        print(f"Process terminated: {error}")

    def on_close(self, ws, status_code, msg):

        df2 = build_dataframe(self.data_lists)
        write_to_csv(df2)
        self.data_lists.clear()
        print(f"Process closed: {status_code}:{msg}")

    def stop(self):
        if self.ws:
            self.ws.close()
            self.thread.join()

    def start(self):
        def run_ws():
            self.ws = websocket.WebSocketApp(
                'wss://data.tradingview.com/socket.io/websocket',
                header=self.headers,
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error)
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        self.thread = threading.Thread(target=run_ws)
        self.thread.start()

# # Example of how to use the class
# if __name__ == "__main__":
#     tv_ws = TradingViewWebSocket()
#     tv_ws.start()
