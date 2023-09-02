
class Tick:
    def __init__(
        self,
        time: int,
        symbol: str,
        volume: int,
        price: float,
        price_change: float,
        is_extended_hours: bool
    ):
        self.time = time
        self.symbol = symbol
        self.volume = volume
        self.price = price
        self.price_change = price_change
        self.is_extended_hours = is_extended_hours

    def __str__(self):
        return (
            f"[{self.time}] {self.symbol} - Volume: {self.volume}, Price: {self.price:.2f}, "
            f"Change: {self.price_change:.2f} ({'Extended Hours' if self.is_extended_hours else 'Regular Hours'})"
        )

    def to_json(self) -> dict:
        return {
            't': self.time,
            's': self.symbol,
            'v': self.volume,
            'p': self.price,
            'pc': self.price_change,
            'ieh': self.is_extended_hours
        }

    @classmethod
    def from_json(cls, json_obj: dict):
        return cls(
            time=json_obj['t'],
            symbol=json_obj['s'],
            volume=json_obj['v'],
            price=json_obj['p'],
            price_change=json_obj['pc'],
            is_extended_hours=json_obj['ieh']
        )
