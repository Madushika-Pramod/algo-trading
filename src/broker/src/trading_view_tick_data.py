import queue
from datetime import datetime

import backtrader as bt

from app.src.voice_alert import voice_alert
from.trading_view_stream import TradingViewWebSocket


class StreamTickData(bt.feed.DataBase):
    lines = ('symbol', 'volume', 'last_price', 'lp_time', 'cumulative_change', 'cc_percentage',"extended_hours_price","ehp_change","close",)

    def __init__(self, q=queue.Queue()):
        super().__init__()
        self.ws = None
        self.data_queue = q

    def start(self):
        self.ws = TradingViewWebSocket(self.data_queue)
        self.ws.start()

    def stop(self):
        self.ws.stop()

    def _load(self):
        try:
            al_data = self.data_queue.get(timeout=120)
            self._map_tick(al_data)
        except queue.Empty:
            voice_alert('say the queue is empty')
            print("queue empty")
            return False
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            voice_alert('say the trading has been terminated', 1)
            return False
        except Exception as e:
            print("An error occurred: ", e)

        return True

    def _map_tick(self, data_dict):
        date_string = data_dict.get('t')
        if date_string and data_dict.get('T') == 't':
            # Trim the string to remove nanoseconds and trailing 'Z'
            date_string_trimmed = date_string[:23]
            # Convert the string to a datetime object
            date = datetime.strptime(date_string_trimmed, '%Y-%m-%dT%H:%M:%S.%f')
            self.lines.datetime[0] = bt.date2num(date)
            self.lines.last_price[0] = data_dict["last_price"]
            self.lines.volume[0] = data_dict["volume"]
            self.lines.cumulative_change[0] = data_dict["cumulative_change"]
            self.lines.cc_percentage[0] = data_dict["cc_percentage"]
            self.lines.extended_hours_price[0] = data_dict["extended_hours_price"]
            self.lines.ehp_change[0] = data_dict["ehp_change"]
            self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = data_dict["last_price"]
