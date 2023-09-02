import asyncio

from aiokafka import AIOKafkaProducer

from pipeline.src.replicator.data_source import CsvDataSource
from pipeline.src.replicator.gateway import MessageGateway
from pipeline.src.replicator.observer import MessageForwarder


async def main():
    async with AIOKafkaProducer(bootstrap_servers="localhost:9090") as producer:
        gateway = MessageGateway(producer=producer)
        forwarder = MessageForwarder(gateway=gateway)

        data_source = CsvDataSource("CSV Reader", "path_to_your_csv_file.csv")
        data_source.add_observer(forwarder)

        await data_source.start_consuming()


if __name__ == "__main__":
    asyncio.run(main())
