import json
import pickle

from pipeline.src.api.message import Message


class MessageSerializer:

    @staticmethod
    def serialize(message: Message) -> bytes:
        """Serialize just the message content to a binary format."""

        try:
            serialized_message_content = message.message.to_json()
        except AttributeError:
            serialized_message_content = json.dumps(message.message, default=str)

        return pickle.dumps(serialized_message_content)

    @staticmethod
    def deserialize(data: bytes, key: str, headers: dict) -> Message:
        """Deserialize the message content from a binary format using external headers."""

        deserialized_message_content = pickle.loads(data)

        obj_type = headers.get("type", None)

        if obj_type:
            message_class = globals().get(obj_type)
            if not message_class:
                raise Exception(f"Type {obj_type} not found during deserialization")

            try:
                message_content = message_class.from_json(deserialized_message_content)
            except AttributeError:
                message_content = json.loads(deserialized_message_content)
        else:
            message_content = deserialized_message_content

        return Message(message=message_content, key=key, metadata=headers)
