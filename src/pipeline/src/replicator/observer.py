import abc

from pipeline.src.api.message import Message
from pipeline.src.replicator.gateway import MessageGateway


class Observer(abc.ABC):
    """Abstract base class for observers."""

    @abc.abstractmethod
    async def update(self, data):
        """Receive update from observable."""
        pass


class MessageForwarder(Observer):
    """An observer that wraps data in a Message envelope and sends it to the MessageGateway."""

    def __init__(self, gateway: MessageGateway):
        self.gateway = gateway

    async def update(self, data):
        """Called when an update is received from the observable."""
        message = Message(data, data)  # Simplified: using data as both message and key
        await self.gateway.send(message)