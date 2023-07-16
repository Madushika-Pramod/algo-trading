from app.src.back_trader import BacktraderStrategy
from strategies import TrendLineStrategy
# from .back_trader import BacktraderStrategy


def run():
    BacktraderStrategy(TrendLineStrategy).run()


if __name__ == "__main__":
    run()
