import logging
import queue
import time
from datetime import datetime

import backtrader as bt

from app.src.notify import news
from app.src.voice_alert import voice_alert
from.trading_view_stream import TradingViewWebSocket

from app.src import constants


class StreamTickData(bt.feed.DataBase):
    lines = ('last_price', 'lp_time', 'cumulative_change', 'cc_percentage', 'extended_hours_price', 'ehp_percentage',)

    # Add a parameter to specify the column position or name of the signal values
    # params = (
    #     ('last_price', -1),('lp_time', -2), ('cumulative_change', -3), ('cc_percentage', -4), ('extended_hours_price', -5), ('ehp_percentage', -6),
    # )

    def __init__(self, q=queue.Queue()):
        # super().__init__()
        self.ws = None
        self.data_queue = q

    def start(self):
        self.ws = TradingViewWebSocket(self.data_queue)
        self.ws.start()

    def stop(self):
        self.ws.stop()

    def _load(self):
        try:
            al_data = self.data_queue.get(timeout=90)

            self._map_tick(al_data)
        except queue.Empty:
            # voice_alert('say the queue is empty')
            logging.warning("⚠️ queue empty")
            news("⚠️ queue empty")
            return False
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt-the trading has been terminated")
            # voice_alert('say the trading has been terminated', 1)
            news("KeyboardInterrupt-the trading has been terminated")

            return False
        except Exception as e:
            logging.error(f"An error occurred from TradingViewStreamData: {e}")
            news(f"An error occurred from TradingViewStreamData: {e}")
            return False

        return True

    def _map_tick(self, data_dict):
        date_string = data_dict.get('t')
        if date_string and data_dict.get('T') == 't':

            # Trim the string to remove nanoseconds and trailing 'Z'
            date_string_trimmed = date_string[:23]

            # Convert the string to a datetime object
            date = datetime.strptime(date_string_trimmed, '%Y-%m-%dT%H:%M:%S.%f')
            self.lines.datetime[0] = bt.date2num(date)
            self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = data_dict["p"]
            self.lines.volume[0] = data_dict["s"]
            # self.tick_data.append(f'{date_string_trimmed}, {data_dict["p"]}, {data_dict["p"]}, {data_dict["p"]}, {data_dict["p"]},{data_dict["p"]}')
            # do this before submit date = datetime.strptime(date_string_trimmed, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            date_string = data_dict.get('timestamp')
            # print(data_dict)
            if date_string:
                self.lines.datetime[0] = bt.date2num(date_string)
                self.lines.open[0] = data_dict['open']
                self.lines.high[0] = data_dict['high']
                self.lines.low[0] = data_dict['low']
                self.lines.close[0] = data_dict['close']
                self.lines.volume[0] = data_dict['volume']

            # else:
            #     date_string = data_dict.get('time') or time.time()
            #
            #     # Convert the string to a datetime object (time in UTC)
            #     date = datetime.utcfromtimestamp(date_string)
            #     self.lines.datetime[0] = bt.date2num(date)
            #
            #     # for store previous data
            #     for key in data_dict.keys():
            #         val = data_dict.get(key)
            #         if val is not None:
            #             constants.trading_view_data[key] = val
            #
            #
            #     self.lines.last_price[0] = self.lines.close[0] = self.lines.low[0] = self.lines.high[0] = self.lines.open[0] = constants.trading_view_data.get('last_price')
            #     self.lines.volume[0] = constants.trading_view_data.get('volume')
            #     self.lines.cumulative_change[0] = constants.trading_view_data.get('p_change')
            #     self.lines.cc_percentage[0] = constants.trading_view_data.get('ch_percentage')
            #     self.lines.extended_hours_price[0] = constants.trading_view_data.get('extended_hours_price')
            #     self.lines.ehp_percentage[0] = constants.trading_view_data.get('ehp_percentage')
