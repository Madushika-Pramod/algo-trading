import unittest
from unittest.mock import patch, AsyncMock

from broker.src.alpaca_trader import alpaca_trade_updates_ws



class TestWebSocket(unittest.TestCase):

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_alpaca_trade_updates_ws(self, mock_connect):
        # Set up the mock for ws.recv
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [
            '{"data": {"event": "new", "order": {"side": "buy", "hwm": "100", "qty": "50", "id": "123"}}}',
            '{"data": {"event": "filled", "order": {"side": "sell", "stop_price": "105", "qty": "50", "id": "124"}}}'
        ]
        mock_connect.return_value.__aenter__.return_value = mock_ws

        # Assuming `state` is an object with two attributes: `pending_order` and `accepted_order`
        state = type('', (), {})()  # Creating a simple mock object for state
        await alpaca_trade_updates_ws(state)

        # You can now make assertions based on your test setup
        self.assertEqual(state.pending_order['id'], '123')
        self.assertEqual(state.accepted_order['id'], '124')

if __name__ == "__main__":
    unittest.main()
