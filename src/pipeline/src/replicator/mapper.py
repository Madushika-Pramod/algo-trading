from pipeline.src.api import Tick


class TradingViewTickToTickMapper:
    @staticmethod
    def from_json(json_ob):
        is_extended_hours = 'rtc' in json_ob and 'rchp' in json_ob

        price = json_ob['rtc'] if is_extended_hours else json_ob['lp']
        price_change = json_ob['rchp'] if is_extended_hours else json_ob['ch']

        return Tick(
            time=json_ob["lp_time"],
            symbol=json_ob["symbol"],
            volume=json_ob['volume'],
            price=price,
            price_change=price_change,
            is_extended_hours=is_extended_hours
        )
