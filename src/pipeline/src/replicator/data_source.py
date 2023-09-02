import abc

import aiofiles

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