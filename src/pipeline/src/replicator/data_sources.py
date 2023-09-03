import abc
import asyncio
import json
import ssl
import re

import aiofiles
import websockets

from pipeline.src.replicator.mapper import TradingViewTickToTickMapper
from pipeline.src.replicator.observer import Observer


class DataSource(abc.ABC):
    """Abstract base class for asynchronous data sources."""

    def __init__(self, name: str):
        self.name = name
        self._observers = []

    def add_observer(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Observer):
        self._observers.remove(observer)

    async def _notify_observers(self, data):
        for observer in self._observers:
            await observer.update(data)

    @abc.abstractmethod
    def __aiter__(self):
        pass

    async def on_data(self, data):
        await self._notify_observers(data)

    async def start_consuming(self):
        async for _ in self:
            pass


class CsvDataSource(DataSource):
    """An asynchronous CSV file reader data source."""

    def __init__(self, name: str, csv_file_path: str):
        super().__init__(name)
        self.csv_file_path = csv_file_path

    def __aiter__(self):
        return self._line_generator()

    async def _line_generator(self):
        async with aiofiles.open(self.csv_file_path, mode='r') as file:
            async for line in file:
                await self.on_data(line.strip())
                yield line.strip()


class TradingViewDataSource:
    def __init__(self, symbol):
        self.symbol = symbol
        self.ws = None
        self.uri = 'wss://data.tradingview.com/socket.io/websocket'
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
        self.queue = asyncio.Queue()

    async def connect(self):
        async with websockets.connect(self.uri, ssl=ssl.CERT_NONE, extra_headers=self.headers) as ws:
            self.ws = ws
            await self.on_open()
            async for message in ws:
                await self.on_message(ws, message)

    async def disconnect(self):
        await self.queue.put(None)

        while not self.queue.empty():
            await self.queue.get()

        if self.ws:
            await self.ws.close()

    async def on_open(self):
        self._ws_send('{"m":"quote_create_session","p":["qs_2YiWuxHOASlh"]}')
        self._ws_send('{"m":"quote_set_fields","p":["qs_2YiWuxHOASlh","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","value_unit_id","rchp","rtc","country_code","provider_id"]}')
        self._ws_send(f'{{"m":"quote_add_symbols","p":["qs_2YiWuxHOASlh","{self.symbol}"]}}')

    def _ws_send(self, message):
        if not isinstance(message, str):
            message = json.dumps(message)  # Convert to string if it's a JSON

        formatted_msg = f"~m~{len(message)}~m~{message}"
        self.ws.send(formatted_msg)

    async def on_message(self, ws, message):
        if message is None or message == "":
            return
        pattern = r"^~m~\d+~m~~h~\d+"
        if re.match(pattern, message):
            ws.send(message)

        else:
            data = self.extract_data(message)
            if data is not None and len(data) > 0:
                self.data_lists.append(data)
                for d in data:
                    self.data_queue.put(d)
        if data is not None and len(data) > 0:
            for d in data:
                await self.queue.put(d)

    def extract_data(self, data):
        data_points = re.split(r'~m~\d+~m~', data)[1:]
        results = []
        pattern = r'((?<=NASDAQ:)\w+).*v":({.+\d})'

        for point in data_points:

            match = re.search(pattern, point)
            if match:
                symbol = match.group(1)
                json_ob = json.loads(match.group(2))
                results.append(TradingViewTickToTickMapper.from_json(json_ob))

        sorted_data = sorted(results, key=lambda x: x['time'])  # sort by time

        return sorted_data

    async def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.queue.get()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()