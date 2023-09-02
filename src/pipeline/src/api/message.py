from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    message: object
    key: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", self.add_metadata({"type": type(self.message).__name__}))

    def add_metadata(self, new_metadata: dict):
        """Returns a new metadata dict updated with the new metadata."""
        updated_metadata = {**self.metadata, **new_metadata}
        return updated_metadata

    def with_metadata(self, new_metadata: dict):
        """Returns a new Message instance with the added metadata."""
        updated_metadata = self.add_metadata(new_metadata)
        return Message(self.message, self.key, updated_metadata)
