import queue
from datetime import datetime

import backtrader as bt

from app.src.voice_alert import voice_alert
from.trading_view_stream import TradingViewWebSocket


class StreamTickData(bt.feed.DataBase):
    lines = ('volume', 'last_price', 'lp_time', 'cumulative_change', 'cc_percentage',"extended_hours_price","ehp_percentage",'close', 'open', 'high', 'low')

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
        date_string = data_dict.get('time')
        if date_string:
            # Convert the string to a datetime object (time in UTC)
            date = datetime.utcfromtimestamp(date_string)

            self.lines.datetime[0] = bt.date2num(date)
            self.lines.last_price[0] = self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = data_dict.get('last_price')
            self.lines.volume[0] = data_dict.get('volume')
            self.lines.cumulative_change[0] = data_dict.get('p_change')
            self.lines.cc_percentage[0] = data_dict.get('ch_percentage')
            self.lines.extended_hours_price[0] = data_dict.get('extended_hours_price')
            self.lines.ehp_percentage[0] = data_dict.get('ehp_percentage')
        else:
            date_string = data_dict.get('timestamp')
            if date_string:
                self.lines.datetime[0] = bt.date2num(date_string)
                self.lines.open[0] = data_dict['open']
                self.lines.high[0] = data_dict['high']
                self.lines.low[0] = data_dict['low']
                self.lines.close[0] = data_dict['close']
                self.lines.volume[0] = data_dict['volume']