import os
import queue
import unittest
from unittest import mock

from app.src.configurations import constants
from app.src.alpaca_data import AlpacaStreamData


class TestAlpacaStreamData(unittest.TestCase):

    def setUp(self):
        # Mock API_KEY and SECRET_KEY in environment variables for tests
        os.environ['API_KEY'] = 'test_api_key'
        os.environ['SECRET_KEY'] = 'test_secret_key'
        self.q = queue.Queue()
        self.rate_limit = constants.time_for_rate_limit
        self.url = constants.market_data_url
        self.symbol = constants.symbol
        self.api_key = os.environ["API_KEY"]
        self.secret_key = os.environ["SECRET_KEY"]

    @mock.patch('threading.Thread')
    def test_start(self, MockThread):
        asd = AlpacaStreamData(q=self.q, rate_limit=self.rate_limit, url=self.url, api_key=self.api_key,
                               secret_key=self.secret_key, symbol=self.symbol)
        asd.start()
        MockThread.assert_called_once_with(target=asd.run)
        asd.thread.start.assert_called_once()

    @mock.patch('requests.get')
    def test_run(self, MockGet):
        mock_response = mock.Mock()
        mock_response.json.return_value = {'trade': 'mock_data'}
        mock_response.text = '{"trade": "mock_data"}'  # This should mimic actual text response

        # Create a list of 5 mock responses
        mock_responses = [mock_response] * 5

        # Use the list as the side_effect for requests.get
        MockGet.side_effect = mock_responses

        asd = AlpacaStreamData(q=self.q, rate_limit=self.rate_limit, url=self.url, api_key=self.api_key,
                               secret_key=self.secret_key, symbol=self.symbol)
        try:
            asd.run()
        except StopIteration:
            pass






    # @mock.patch('queue.Queue.get')
    # def test_load(self, MockGet):
    #
    #     mock_data_formats = [
    #         {"symbol": "AAPL",
    #          "trade": {"t": "2023-07-11T19:59:59.729124241Z", "x": "V", "p": 188.05, "s": 200, "c": ["@"], "i": 7970,
    #                    "z": "C"}}
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.72912Z", "x": "V", "p": 188.05, "s": 870, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.7296986924241Z", "x": "V", "p": 188.05, "s": 204, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.72Z", "x": "V", "p": 169.05, "s": 280, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.728089124241Z", "x": "V", "p": 198.05, "s":450, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.7291Z", "x": "V", "p": 200, "s": 870, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.729124Z", "x": "V", "p": 188.05, "s": 120, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #         # {"symbol": "AAPL",
    #         #  "trade": {"t": "2023-07-11T19:59:59.72912Z", "x": "V", "p": 188.05, "s": 90, "c": ["@"], "i": 7970,
    #         #            "z": "C"}},
    #
    #         # Add different timestamp formats here
    #     ]
    #
    #     for mock_data in mock_data_formats:
    #         MockGet.return_value = mock_data
    #
    #         asd = AlpacaStreamData(q=self.q, rate_limit=self.rate_limit, url=self.url, api_key=self.api_key,
    #                                secret_key=self.secret_key, symbol=self.symbol)
    #         result = asd._load()

            # self.assertTrue(result)

        #     dt_str = mock_data["trade"]["t"]
        #     # Update the following code to handle different timestamp formats as necessary
        #     parts = dt_str.split('.')
        #     dt_str = "{:.6f}".format(float("0." + parts[1][:-1])) + "+00:00"
        #     dt = datetime.fromisoformat(parts[0] + dt_str[1:])  # Convert string to datetime object
        #     float_timestamp = date2num(dt)
        #
        #     self.assertEqual(asd.lines.datetime[0], float_timestamp)
        #     self.assertEqual(asd.lines.close[0], mock_data["trade"]["p"])
        #     self.assertEqual(asd.lines.low[0], mock_data["trade"]["p"])
        #     self.assertEqual(asd.lines.high[0], mock_data["trade"]["p"])
        #     self.assertEqual(asd.lines.open[0], mock_data["trade"]["p"])
        #     self.assertEqual(asd.lines.volume[0], mock_data["trade"]["s"])
