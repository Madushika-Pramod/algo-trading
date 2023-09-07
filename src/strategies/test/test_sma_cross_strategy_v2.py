# import unittest
# from unittest.mock import MagicMock, patch, PropertyMock, Mock
#
# from app.src.back_trader import BacktraderStrategy
# from strategies import SmaCrossstrategyV2
#
#
# # def mock_dataframe():
# #     import pandas as pd
# #     data = """symbol,timestamp,open,high,low,close,volume,trade_count,vwap
# # TSLA,2023-08-21 10:52:00+00:00,222.4,222.45,222.4,222.45,2001.0,97.0,222.423308
# # TSLA,2023-08-21 10:53:00+00:00,222.4,222.4,222.35,222.4,1671.0,57.0,222.394375
# # TSLA,2023-08-21 10:54:00+00:00,222.36,222.77,222.36,222.77,17432.0,135.0,222.532396
# # TSLA,2023-08-21 10:55:00+00:00,222.71,222.72,222.47,222.47,5089.0,114.0,222.611666
# # TSLA,2023-08-21 10:56:00+00:00,222.46,222.6,222.46,222.6,1614.0,55.0,222.541561
# # TSLA,2023-08-21 10:57:00+00:00,222.51,222.51,222.47,222.48,3693.0,92.0,222.503826
# # TSLA,2023-08-21 10:58:00+00:00,222.49,222.6,222.49,222.54,3761.0,83.0,222.542223
# # TSLA,2023-08-21 10:59:00+00:00,222.55,222.6,222.42,222.42,7570.0,201.0,222.552157
# # TSLA,2023-08-21 11:00:00+00:00,222.42,222.58,221.9,221.91,48216.0,1167.0,222.114586
# # TSLA,2023-08-21 11:01:00+00:00,221.81,220.11,221.81,221.96,22691.0,362.0,221.963099
# # TSLA,2023-08-21 11:02:00+00:00,221.99,222.07,221.85,221.85,12591.0,182.0,221.975099
# # TSLA,2023-08-21 11:03:00+00:00,221.81,222.0,221.7,222.0,27258.0,423.0,221.799259
# # TSLA,2023-08-21 11:04:00+00:00,222.0,222.4,222.0,222.4,15782.0,294.0,222.18737
# # TSLA,2023-08-21 11:05:00+00:00,222.38,222.7,222.38,222.59,19029.0,287.0,222.580418
# # TSLA,2023-08-21 11:06:00+00:00,222.56,222.56,222.4,222.4,5703.0,133.0,222.510119
# # TSLA,2023-08-21 11:07:00+00:00,222.4,222.41,222.25,222.25,2562.0,84.0,222.357151
# # TSLA,2023-08-21 11:08:00+00:00,222.22,222.35,222.22,222.35,3076.0,96.0,222.283703
# # TSLA,2023-08-21 11:09:00+00:00,222.38,222.45,222.38,222.4,5722.0,110.0,222.417681
# # TSLA,2023-08-21 11:10:00+00:00,222.4,222.4,222.2,222.2,7442.0,113.0,222.291907
# # TSLA,2023-08-21 11:11:00+00:00,222.2,222.2,221.91,221.91,9203.0,229.0,222.072537
# # TSLA,2023-08-21 11:12:00+00:00,221.96,221.96,221.9,221.95,4155.0,130.0,221.919292
# # TSLA,2023-08-21 11:13:00+00:00,222.0,222.03,222.0,222.03,2754.0,74.0,222.044089
# # TSLA,2023-08-21 11:14:00+00:00,222.2,222.2,222.11,222.11,1532.0,57.0,222.158538
# # TSLA,2023-08-21 11:15:00+00:00,222.06,222.09,222.0,222.0,5071.0,148.0,222.047478
# # TSLA,2023-08-21 11:16:00+00:00,221.98,222.25,221.93,222.25,10071.0,164.0,222.079447
# # TSLA,2023-08-21 11:17:00+00:00,222.29,222.38,222.25,222.25,5591.0,117.0,222.309426
# # TSLA,2023-08-21 11:18:00+00:00,222.29,222.32,222.29,222.32,2266.0,67.0,222.30462
# # TSLA,2023-08-21 11:19:00+00:00,222.35,222.5,222.35,222.5,5375.0,129.0,222.402125
# # TSLA,2023-08-21 11:20:00+00:00,222.49,222.5,222.45,222.45,3269.0,77.0,222.461383
# # TSLA,2023-08-21 11:21:00+00:00,222.41,222.41,222.25,222.33,4694.0,104.0,222.339146
# # TSLA,2023-08-21 11:22:00+00:00,222.33,222.33,222.32,222.33,2707.0,64.0,222.312612
# # TSLA,2023-08-21 11:23:00+00:00,222.31,222.31,222.25,222.25,3150.0,77.0,222.257683
# # TSLA,2023-08-21 11:24:00+00:00,222.14,222.2,222.12,222.13,5691.0,133.0,222.156547"""
# #
# #     df = pd.read_csv(StringIO(data), sep=",")
# #
# #     last_data = {
# #         'symbol': ['TSLA'],
# #         'timestamp': ['2023-08-21 11:25:00+00:00'],
# #         'open': [222.13],
# #         'high': [222.19],
# #         'low': [222.11],
# #         'close': [222.11],
# #         'volume': [1586.0],
# #         'trade_count': [58.0],
# #         'vwap': [222.141482]
# #     }
# #     df_new = pd.DataFrame(last_data)
# #     df = pd.concat([df_new, df], ignore_index=True)
# #     df['timestamp'] = pd.to_datetime(df['timestamp'])
# #
# #     return df
#
#
# class MockedSmaCrossstrategyV2(SmaCrossstrategyV2):
#
#     def __init__(self):
#         super().__init__(trader=MagicMock())
#
#     def next(self):
#         return
#
#
# class TestSmaCrossStrategyV2(unittest.TestCase):
#
#
#     # @patch.object(MockedSmaCrossstrategyV2, 'starting_balance', new_callable=PropertyMock, create=True)
#     # @patch.object(MockedSmaCrossstrategyV2, 'cumulative_profit', new_callable=PropertyMock, create=True)
#     # def test_roi(self, mock_cumulative_profit, mock_starting_balance):
#     #     mock_cumulative_profit.return_value = 10
#     #     mock_starting_balance.return_value = 100
#     #
#     #     b = BacktraderStrategy(False, cash=5000)
#     #     roi = b.add_strategy((MockedSmaCrossstrategyV2, {})).run().total_return_on_investment
#     #     self.assertEqual(roi, 0.1)
#
#     def setUp(self):
#         # with patch('backtrader.Strategy', new_callable=Mock) as MockedStrategy:
#         #     # Mocking every method and attribute
#         #     instance = MockedStrategy.return_value
#         #
#         #     # For instance, if you want every method to return "Mocked Value":
#         #     instance.some_method.return_value = "Mocked Value"
#         #     instance.some_attribute = "Mocked Attribute"
#         #
#         #     self.strategy = SmaCrossstrategyV2()
#         #     self.strategy.data = MagicMock()
#         #     self.strategy.data.close = [100]
#         #     self.strategy.data.volume = [100000]
#         #     self.strategy.moving_avg_crossover_indicator = 0
#         #     self.strategy.recorded_highest_price = [150]
#         #     self.strategy.recorded_lowest_price = [50]
#         #     # self.strategy.trader = MagicMock()
#         #     self.strategy.price_of_last_sale = 110
#         #     self.strategy.price_of_last_purchase = 90
#
#     def test_roi(self):
#         self.strategy.cumulative_profit = 100
#         self.strategy.starting_balance = 1000
#         self.assertEqual(self.strategy._roi(), 0.1)
#
#     # def test_is_initial_buy_condition(self):
#     #     self.strategy.trade_active = None
#     #     constants.min_price = 9.0
#     #     self.assertTrue(self.strategy._is_initial_buy_condition())
#     #
#     # def test_is_price_near_lowest(self):
#     #     self.strategy.recorded_lowest_price = [9.0]
#     #     self.strategy.p.high_low_tolerance = 1.1
#     #     self.assertTrue(self.strategy._is_price_near_lowest())
#     #
#     # def test_is_price_near_highest(self):
#     #     self.strategy.recorded_highest_price = [11.0]
#     #     self.strategy.p.high_low_tolerance = 1.1
#     #     self.assertFalse(self.strategy._is_price_near_highest())
#     #
#     # def test_profit(self):
#     #     self.strategy.price_of_last_purchase = 8.0
#     #     self.strategy.p.sell_profit_threshold = 2.0
#     #     self.assertTrue(self.strategy._profit())
#     #
#     # @patch("your_module_path.logging.info")
#     # def test_start_buy_process_live_mode(self, mock_log):
#     #     self.strategy.live_mode = True
#     #     self.strategy.ready_to_buy = True
#     #     self.strategy.data.volume = [constants.median_volume + 1]
#     #     self.strategy.moving_avg_crossover_indicator = 1
#     #     self.strategy._start_buy_process()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.critical")
#     # def test_halt_trading_and_alert(self, mock_log):
#     #     self.strategy.price_of_last_purchase = 12.0
#     #     constants.loss_value = 10.0
#     #     self.strategy.data.close = [1.0]
#     #     with self.assertRaises(Exception):
#     #         self.strategy._halt_trading_and_alert()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.info")
#     # def test_start_sell_process_live_mode(self, mock_log):
#     #     self.strategy.live_mode = True
#     #     self.strategy.ready_to_sell = True
#     #     self.strategy.data.volume = [constants.median_volume + 1]
#     #     self.strategy.moving_avg_crossover_indicator = -1
#     #     self.strategy._start_sell_process()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.critical")
#     # def test_alert_no_sell(self, mock_log):
#     #     self.strategy._alert_no_sell()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.critical")
#     # def test_alert_no_buy(self, mock_log):
#     #     self.strategy._alert_no_buy()
#     #     mock_log.assert_called()
#     #
#     # def test_check_loss_value(self):
#     #     self.strategy.price_of_last_purchase = 20.0
#     #     constants.loss_value = 15.0
#     #     self.strategy.data.close = [14.0]
#     #     with self.assertRaises(Exception):
#     #         self.strategy._check_loss_value()
#     #
#     # def test_take_profit_or_stop_loss(self):
#     #     self.strategy.price_of_last_purchase = 8.0
#     #     self.strategy.p.sell_profit_threshold = 2.0
#     #     self.strategy.data.close = [17.0]  # Significant profit
#     #     self.assertTrue(self.strategy._take_profit_or_stop_loss())
#     #
#     #     self.strategy.data.close = [6.0]  # Loss scenario
#     #     self.assertTrue(self.strategy._take_profit_or_stop_loss())
#     #
#     # def test_get_smallest_price(self):
#     #     self.strategy.recorded_lowest_price = [10.0, 8.0, 9.0, 7.5, 11.0]
#     #     self.assertEqual(self.strategy._get_smallest_price(), 7.5)
#     #
#     # def test_get_largest_price(self):
#     #     self.strategy.recorded_highest_price = [10.0, 8.0, 9.0, 7.5, 11.0]
#     #     self.assertEqual(self.strategy._get_largest_price(), 11.0)
#     #
#     # # Assuming _record_price takes the current price and adds it to the relevant list.
#     # def test_record_price(self):
#     #     self.strategy.data.close = [12.0]
#     #     self.strategy._record_price()
#     #     self.assertIn(12.0, self.strategy.recorded_lowest_price)
#     #     self.assertIn(12.0, self.strategy.recorded_highest_price)
#     #
#     # @patch("your_module_path.logging.info")
#     # def test_start_sell_process_live_mode(self, mock_log):
#     #     self.strategy.live_mode = True
#     #     self.strategy.ready_to_sell = True
#     #     self.strategy.data.volume = [constants.median_volume + 1]
#     #     self.strategy.moving_avg_crossover_indicator = -1
#     #     self.strategy._start_sell_process()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.critical")
#     # def test_alert_no_sell(self, mock_log):
#     #     self.strategy._alert_no_sell()
#     #     mock_log.assert_called()
#     #
#     # @patch("your_module_path.logging.critical")
#     # def test_alert_no_buy(self, mock_log):
#     #     self.strategy._alert_no_buy()
#     #     mock_log.assert_called()
#     #
#     # def test_check_loss_value(self):
#     #     self.strategy.price_of_last_purchase = 20.0
#     #     constants.loss_value = 15.0
#     #     self.strategy.data.close = [14.0]
#     #     with self.assertRaises(Exception):
#     #         self.strategy._check_loss_value()
#     #
#     # def test_take_profit_or_stop_loss(self):
#     #     self.strategy.price_of_last_purchase = 8.0
#     #     self.strategy.p.sell_profit_threshold = 2.0
#     #     self.strategy.data.close = [17.0]  # Significant profit
#     #     self.assertTrue(self.strategy._take_profit_or_stop_loss())
#     #
#     #     self.strategy.data.close = [6.0]  # Loss scenario
#     #     self.assertTrue(self.strategy._take_profit_or_stop_loss())
#     #
#     # def test_get_smallest_price(self):
#     #     self.strategy.recorded_lowest_price = [10.0, 8.0, 9.0, 7.5, 11.0]
#     #     self.assertEqual(self.strategy._get_smallest_price(), 7.5)
#     #
#     # def test_get_largest_price(self):
#     #     self.strategy.recorded_highest_price = [10.0, 8.0, 9.0, 7.5, 11.0]
#     #     self.assertEqual(self.strategy._get_largest_price(), 11.0)
#     #
#     # # Assuming _record_price takes the current price and adds it to the relevant list.
#     # def test_record_price(self):
#     #     self.strategy.data.close = [12.0]
#     #     self.strategy._record_price()
#     #     self.assertIn(12.0, self.strategy.recorded_lowest_price)
#     #     self.assertIn(12.0, self.strategy.recorded_highest_price)
#     #
#     # # def test_roi(self):
#     # #     self.strategy.cumulative_profit = 100
#     # #     self.strategy.starting_balance = 1000
#     # #     self.assertEqual(self.strategy._roi(), 0.1)
#     #
#     # def test_is_initial_buy_condition(self):
#     #     self.strategy.trade_active = None
#     #     self.strategy.data.close[0] = 5
#     #     self.assertTrue(self.strategy._is_initial_buy_condition())
#     #
#     # def test_buy_orders_ready_on_alpaca(self):
#     #     self.strategy.algorithm_performed_buy_order_id = '123'
#     #     self.strategy.constants.accepted_order = {'id': '123'}
#     #     self.assertTrue(self.strategy._buy_orders_ready_on_alpaca())
#     #
#     # def test_execute_buy_orders(self):
#     #     with patch('your_script_name.logging') as mock_logging:  # Adjust your_script_name to your actual script name
#     #         self.strategy._execute_buy_orders()
#     #         mock_logging.info.assert_called_with("177 -buy executed")
#     #         self.strategy.trader.buy.assert_not_called()  # Ensure no live trades are executed
#     #         self.assertEqual(self.strategy.price_of_last_purchase,
#     #                          float(self.strategy.constants.accepted_order['stop_price']))
#     #
#     # @patch('your_module_path.constants')
#     # def test_is_initial_buy_condition(self, mock_constants):
#     #     mock_constants.min_price = 10
#     #     self.strategy.trade_active = None
#     #     self.strategy.data.close = [9]
#     #     self.assertTrue(self.strategy._is_initial_buy_condition())
#     #
#     # @patch('your_module_path.constants')
#     # def test_buy_orders_ready_on_alpaca(self, mock_constants):
#     #     mock_constants.accepted_order = {'id': '123'}
#     #     self.strategy.algorithm_performed_buy_order_id = '123'
#     #     self.assertTrue(self.strategy._buy_orders_ready_on_alpaca())
#     #
#     # def test_execute_buy_orders(self):
#     #     with patch('your_module_path.constants.accepted_order', {'stop_price': '10.5'}):
#     #         self.strategy.buy = MagicMock()
#     #         self.strategy._reset_buy_state = MagicMock()
#     #         self.strategy._execute_buy_orders()
#     #         self.strategy.buy.assert_called_once()
#     #         self.strategy._reset_buy_state.assert_called_once()
#     #         self.assertEqual(self.strategy.price_of_last_purchase, 10.5)
#     #
#     # def test_need_to_cancel_buy_order(self):
#     #     self.strategy.trade_active = False
#     #     self.strategy.data.close = [20]
#     #     with patch('your_module_path.constants.pending_order', {'hwm': '50'}):
#     #         self.strategy.p.buy_profit_threshold = 4
#     #         self.assertTrue(self.strategy._need_to_cancel_buy_order())
#     #
#     # def test_cancel_buy_order(self):
#     #     with patch('your_module_path.constants.pending_order', {'hwm': '50', 'id': '123'}):
#     #         self.strategy._cancel_order = MagicMock()
#     #         self.strategy._cancel_buy_order()
#     #         self.strategy._cancel_order.assert_called_once_with('123')
#     #
#     # def test_halt_trading_and_alert(self):
#     #     self.strategy.trader = MagicMock()
#     #     self.strategy.stop = MagicMock()
#     #     with self.assertRaises(Exception):
#     #         self.strategy._halt_trading_and_alert()
#     #     self.strategy.trader.trading_client.close_all_positions.assert_called_once()
#     #
#     # # Example for a method called 'compute_sma'
#     # def test_compute_sma(self):
#     #     # Mocking data to be used in the method
#     #     self.strategy.data = MagicMock()
#     #     self.strategy.data.close = [1, 2, 3, 4, 5]
#     #
#     #     # Assuming compute_sma returns the average of the above data
#     #     result = self.strategy.compute_sma()
#     #     self.assertEqual(result, 3)
#     #
#     # # Example for a method called 'place_order'
#     # def test_place_order(self):
#     #     with patch('your_module_path.SomeExternalAPI') as MockAPI:
#     #         # Assume the API has a method 'order' that the place_order method calls
#     #         instance = MockAPI.return_value
#     #         instance.order.return_value = {'status': 'success'}
#     #
#     #         result = self.strategy.place_order(100, 'buy')
#     #
#     #         instance.order.assert_called_once_with(100, 'buy')
#     #         self.assertEqual(result, {'status': 'success'})
#
#
# if __name__ == '__main__':
#     unittest.main()
