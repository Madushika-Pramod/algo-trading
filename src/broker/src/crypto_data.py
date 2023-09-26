import csv
import logging
import os
from datetime import datetime, timedelta

from alpaca.data import CryptoHistoricalDataClient, CryptoBarsRequest, TimeFrame

from app.src import constants


class AlpacaCryptoHistoricalData:
    def __init__(self, symbol, period_in_days, csv_file_path):
        self.csv_file_path = csv_file_path
        self.symbol = symbol
        self.days = period_in_days
        self.client = CryptoHistoricalDataClient(os.environ.get("API_KEY"), os.environ.get("SECRET_KEY"))

    def get_stock_historical_data(self, period=constants.time_frame):
        t_frame = TimeFrame.Minute
        # if period == "hour":
        #     t_frame = TimeFrame.Hour
        # elif period == "minute":
        #     t_frame = TimeFrame.Minute

        start_date = datetime.now() - timedelta(days=self.days)
        #  Sri lanka is 5 hours and 30 minutes ahead of UTC + 15 min
        # todo check this on none trading time
        end_date = datetime.now() - timedelta(minutes=345)
        request_params = CryptoBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=t_frame,
            start=start_date.isoformat(),
            end=end_date.isoformat())

        return self.client.get_crypto_bars(request_params, feed='us').data

    def save_to_csv(self, data=None):
        bars = data or self.get_stock_historical_data()
        header = list(dict(bars[self.symbol][0]).keys())

        with open(self.csv_file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()

            for entry in bars[self.symbol]:
                writer.writerow(dict(entry))

        logging.info("Data has been written to '{}' file.".format(self.csv_file_path))


AlpacaCryptoHistoricalData("LINK/USD", 1, constants.crypto_file_path).save_to_csv()
