import os
import pytest
from unittest.mock import patch
from app import app, client, get_account_balance, get_open_orders, get_recent_trades, handle_place_order, handle_cancel_order
from flask_socketio import SocketIO
from binance.exceptions import BinanceAPIException
from binance.client import Client

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "test_api_key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test_api_secret")

# Mock Binance client
@pytest.fixture
def mock_binance_client():
    with patch('app.Client') as mock_client:
        yield mock_client

#Test cases
def test_valid_api_keys(mock_binance_client):
    mock_binance_client.return_value.get_exchange_info.return_value = {'symbols': [{'symbol': 'BTCUSDT'}]}
    mock_binance_client.return_value.get_account.return_value = {'balances': [{'asset': 'BTC', 'free': '1', 'locked': '0'}]}
    mock_binance_client.return_value.get_open_orders.return_value = []
    mock_binance_client.return_value.get_my_trades.return_value = []
    app.config['TESTING'] = True
    with app.test_client() as c:
        assert c.get('/api/symbols').json == ['BTCUSDT']
        assert len(get_account_balance()) > 0
        assert len(get_open_orders()) == 0
        assert len(get_recent_trades('BTCUSDT')) == 0

def test_invalid_api_keys(mock_binance_client):
    mock_binance_client.side_effect = BinanceAPIException("Invalid API Key")
    with pytest.raises(BinanceAPIException):
        get_account_balance()

def test_place_order_success(mock_binance_client):
    mock_binance_client.return_value.create_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 123, 'type': 'LIMIT', 'side': 'BUY', 'price': '10000', 'origQty': '1', 'executedQty': '1', 'status': 'FILLED', 'time': 1678886400000}
    mock_binance_client.return_value.get_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 123, 'type': 'LIMIT', 'side': 'BUY', 'price': '10000', 'origQty': '1', 'executedQty': '1', 'status': 'FILLED', 'time': 1678886400000}
    mock_binance_client.return_value.get_account.return_value = {'balances': [{'asset': 'BTC', 'free': '1', 'locked': '0'}]}
    mock_binance_client.return_value.get_open_orders.return_value = []
    mock_binance_client.return_value.get_my_trades.return_value = []

    socketio = SocketIO(app)
    with patch('app.emit') as mock_emit:
      handle_place_order({'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': '1', 'price': '10000'})
      mock_emit.assert_called_with('order_response', {'success': True, 'order': {'symbol': 'BTCUSDT', 'orderId': 123, 'type': 'LIMIT', 'side': 'BUY', 'price': '10000.00000000', 'origQty': '1.00000000', 'executedQty': '1.00000000', 'status': 'FILLED', 'time': '2023-03-15 00:00:00'}})

def test_place_order_failure(mock_binance_client):
    mock_binance_client.return_value.create_order.side_effect = BinanceAPIException("-1013: Invalid quantity")
    socketio = SocketIO(app)
    with patch('app.emit') as mock_emit:
        handle_place_order({'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': '1', 'price': '10000'})
        mock_emit.assert_called_with('order_response', {'success': False, 'error': '-1013: Invalid quantity'})

def test_cancel_order_success(mock_binance_client):
    mock_binance_client.return_value.cancel_order.return_value = {}
    mock_binance_client.return_value.get_account.return_value = {'balances': [{'asset': 'BTC', 'free': '1', 'locked': '0'}]}
    mock_binance_client.return_value.get_open_orders.return_value = []
    socketio = SocketIO(app)
    with patch('app.emit') as mock_emit:
        handle_cancel_order({'symbol': 'BTCUSDT', 'orderId': 123})
        mock_emit.assert_called_with('cancel_response', {'success': True})

def test_cancel_order_failure(mock_binance_client):
    mock_binance_client.return_value.cancel_order.side_effect = BinanceAPIException("-2011: Order not found")
    socketio = SocketIO(app)
    with patch('app.emit') as mock_emit:
        handle_cancel_order({'symbol': 'BTCUSDT', 'orderId': 123})
        mock_emit.assert_called_with('cancel_response', {'success': False, 'error': '-2011: Order not found'})