import json
import logging
import threading
import unittest
from unittest.mock import patch, AsyncMock

from broker.src.alpaca_trader import alpaca_trade_updates_ws, get_trade_updates
from strategies.src.sma.sma_cross_strategy import _State


async def mock_alpaca_trade_updates_ws(state):
    print('mock trades started')
    # Mock data to simulate WebSocket messages
    mock_messages = [
        '{"data": {"event": "new", "order": {"id": "123", "side": "buy", "hwm": "100", "qty": "10"}}}',
        # '{"data": {"event": "accepted", "order": {"id": "order2", "side": "sell", "hwm": "101", "qty": "5"}}}',
        '{"data": {"event": "filled", "order": {"id": "124", "side": "buy", "stop_price": "99", "qty": "2"}}}',
        # '{"data": {"event": "canceled", "order": {"id": "order4", "side": "sell", "stop_price": "102", "qty": "8"}}}'
    ]

    # Simulating authentication and listening setup
    print("Mock authentication and listening setup complete.")

    # Simulate receiving trade updates
    for message in mock_messages:
        print(f'trade update: {message}')
        trade = json.loads(message)['data']

        if trade['event'] == 'new' or trade['event'] == 'accepted':
            state.accepted_order = trade['order']
            logging.info(f'pending_order.id:{state.accepted_order.id}')
            logging.info(
                f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['hwm']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            print(
                f"event type: {trade['event']}\na {trade['order']['side']} order is placed at price {trade['order']['hwm']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

        elif trade['event'] == 'filled' or trade['event'] == 'partial_fill':
            state.filled_order = trade['order']
            logging.info(f'executed_order.id:{state.filled_order.id}')
            logging.info(
                f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            print(
                f"event type: {trade['event']}\na {trade['order']['side']} order is executed at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

        elif trade['event'] == 'canceled':
            logging.info(
                f"event type: {trade['event']}\na {trade['order']['side']} order is canceled at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")
            print(
                f"event type: {trade['event']}\na {trade['order']['side']} order is canceled at price {trade['order']['stop_price']} with {trade['order']['qty']} of quantity\nOrder id={trade['order']['id']}")

        else:
            logging.info(f"alpaca event > event type: {trade['event']}")
            print(f"alpaca event > event type: {trade['event']}")

    # To simulate continuous updates, uncomment this loop:
    # while True:
    #     message = '{"data": {"event": "random_event"}}'
    #     print(f'trade update: {message}')
    #     await asyncio.sleep(5)


class AlpacaWSTest(unittest.TestCase):

    # @patch('broker.src.alpaca_trader.alpaca_trade_updates_ws', )
    def test_alpaca_trade_updates_ws(self):
        with patch('broker.src.alpaca_trader.alpaca_trade_updates_ws', mock_alpaca_trade_updates_ws):
            self.state = _State(1000)
            thread = threading.Thread(target=get_trade_updates, args=(self.state,))  # start trade updates
            thread.start()
            self.assertEqual(self.state.accepted_order['id'], '123')
            self.assertEqual(self.state.filled_order['id'], '124')
class TestWebSocket(unittest.TestCase):

    def test_alpaca_trade_updates(self):
        self.state = _State(1000)
        thread = threading.Thread(target=get_trade_updates, args=(self.state,))  # start trade updates
        thread.start()
        self.assertEqual(self.state.accepted_order['id'], '123')
        self.assertEqual(self.state.filled_order['id'], '124')




    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_alpaca_trade_updates_ws(self, mock_connect):
        # Set up the mock for ws.recv
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [
            '{"data": {"event": "new", "order": {"side": "buy", "hwm": "100", "qty": "50", "id": "123"}}}',
            '{"data": {"event": "filled", "order": {"side": "sell", "stop_price": "105", "qty": "50", "id": "124"}}}'
        ]
        mock_connect.return_value.__aenter__.return_value = mock_ws

        # # Assuming `state` is an object with two attributes: `pending_order` and `accepted_order`
        # state = type('', (), {})()  # Creating a simple mock object for state
        # await alpaca_trade_updates_ws(state)
        #
        # # You can now make assertions based on your test setup
        # self.assertEqual(state.pending_order['id'], '123')
        # self.assertEqual(state.accepted_order['id'], '124')



if __name__ == "__main__":
    unittest.main()
