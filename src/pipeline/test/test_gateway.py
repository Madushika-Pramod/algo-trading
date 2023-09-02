import unittest
from unittest.mock import AsyncMock, Mock
import asyncio

from pipeline.src.replicator.gateway import MessageGateway


class TestMessageGateway(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_send(self):
        # Mocks
        producer_mock = AsyncMock()
        message_mock = Mock()
        message_mock.metadata = {"provider": "test_provider"}
        message_mock.key = "test_key"
        message_mock.serialize.return_value = b"test_serialized_data"

        # Create an instance of the MessageGateway
        gateway = MessageGateway(producer=producer_mock, hostname_provider=lambda: "test_hostname")

        # Since unittest doesn't natively support asyncio, run the coroutine using the event loop
        self.loop.run_until_complete(gateway.send(message_mock))

        # Asserts
        message_mock.serialize.assert_called_once()

        producer_mock.send_and_wait.assert_called_once_with(
            "test_key",
            value=b"test_serialized_data",
            headers=[
                ("provider", "test_provider".encode('utf-8')),
                ("timestamp", Mock.ANY),
                ("machine", "test_hostname".encode('utf-8'))
            ]
        )