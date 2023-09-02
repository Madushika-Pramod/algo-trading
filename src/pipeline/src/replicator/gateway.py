from aiokafka import AIOKafkaProducer
from datetime import datetime
import socket

from pipeline.src.api.message import Message
from pipeline.src.replicator.serializers import MessageSerializer


class MessageGateway:
    def __init__(self, producer: AIOKafkaProducer, hostname_provider=None):
        self.producer = producer
        self.hostname_provider = hostname_provider or socket.gethostname

    async def send(self, message: Message):
        """Send a Message to Kafka, using metadata in the headers."""
        provider = message.metadata.get("provider", "unknown")
        serialized_data = MessageSerializer.serialize(message)

        headers = [
            ("provider", provider.encode('utf-8')),
            ("timestamp", str(datetime.now().timestamp()).encode('utf-8')),
            ("machine", self.hostname_provider().encode('utf-8'))
        ]

        await self.producer.send_and_wait(message.key, value=serialized_data, headers=headers)
