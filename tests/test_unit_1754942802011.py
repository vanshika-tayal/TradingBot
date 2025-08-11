import os
import pytest
from unittest.mock import patch
from app import app, client, get_account_balance, get_open_orders, get_recent_trades, handle_place_order
from flask_socketio import SocketIO
from binance.exceptions import BinanceAPIException
from binance.client import Client

@pytest.fixture
def socketio_client(request):
    test_client = app.test_client()
    socketio = SocketIO(app)
    socketio.init_app(app)
    socketio.run(app, debug=False)
    yield test_client

@pytest.fixture(autouse=True)
def environment_variables():
    os.environ['BINANCE_API_KEY'] = 'test_api_key'
    os.environ['BINANCE_API_SECRET'] = 'test_api_secret'

@patch('app.Client')
def test_invalid_api_key(mock_client):
    os.environ['BINANCE_API_KEY'] = 'invalid_api_key'
    with pytest.raises(Exception) as e:
        client
    assert "Failed to initialize Binance client" in str(e.value)

@patch('app.Client')
def test_invalid_api_secret(mock_client):
    os.environ['BINANCE_API_SECRET'] = 'invalid_api_secret'
    with pytest.raises(Exception) as e:
        client
    assert "Failed to initialize Binance client" in str(e.value)

@patch('app.Client.get_account')
def test_get_account_balance(mock_get_account):
    mock_get_account.return_value = {'balances': [{'asset': 'BTC', 'free': '1.0', 'locked': '0.0'}]}
    balance = get_account_balance()
    assert balance == {'BTC': {'free': '1.00000000', 'locked': '0.00000000'}}

@patch('app.Client.get_open_orders')
def test_get_open_orders(mock_get_open_orders):
    mock_get_open_orders.return_value = [{'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'origQty': '1', 'executedQty': '0', 'status': 'NEW'}]
    orders = get_open_orders()
    assert len(orders) == 1
    assert orders[0]['symbol'] == 'BTCUSDT'

@patch('app.Client.get_my_trades')
def test_get_recent_trades(mock_get_my_trades):
    mock_get_my_trades.return_value = [{'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'qty': '1', 'commission': '0.001'}]
    trades = get_recent_trades('BTCUSDT')
    assert len(trades) == 1
    assert trades[0]['symbol'] == 'BTCUSDT'

@patch('app.Client.create_order')
@patch('app.Client.get_order')
def test_handle_place_order_market(mock_get_order, mock_create_order, socketio_client):
    mock_create_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 456, 'executedQty': '1', 'cummulativeQuoteQty': '10000'}
    mock_get_order.return_value = mock_create_order.return_value
    with patch('app.emit') as mock_emit:
        handle_place_order({'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '1'})
        mock_emit.assert_any_call('order_response', {'success': True, 'order': {'symbol': 'BTCUSDT', 'orderId': 456, 'type': 'MARKET', 'side': 'BUY', 'price': '10000.00000000', 'origQty': '1.00000000', 'executedQty': '1.00000000', 'status': 'FILLED', 'time': '2024-07-27 12:00:00'}})

@patch('app.Client.create_order')
def test_handle_place_order_limit(mock_create_order, socketio_client):
    mock_create_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 456, 'executedQty': '0', 'status': 'NEW', 'price': '10000'}
    with patch('app.emit') as mock_emit:
        handle_place_order({'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': '1', 'price': '10000'})
        mock_emit.assert_any_call('order_response', {'success': True, 'order': {'symbol': 'BTCUSDT', 'orderId': 456, 'type': 'LIMIT', 'side': 'BUY', 'price': '10000.00000000', 'origQty': '1.00000000', 'executedQty': '0.00000000', 'status': 'NEW', 'time': '2024-07-27 12:00:00'}})

@patch('app.Client.cancel_order')
def test_handle_cancel_order(mock_cancel_order, socketio_client):
    mock_cancel_order.return_value = {}
    with patch('app.emit') as mock_emit:
        handle_place_order({'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'LIMIT', 'quantity': '1', 'price': '10000'})
        handle_cancel_order({'symbol': 'BTCUSDT', 'orderId': 456})
        mock_emit.assert_any_call('cancel_response', {'success': True})

@patch('app.Client.cancel_order')
def test_handle_cancel_order_failure(mock_cancel_order, socketio_client):
    mock_cancel_order.side_effect = BinanceAPIException(-1, 'Order not found')
    with patch('app.emit') as mock_emit:
        handle_cancel_order({'symbol': 'BTCUSDT', 'orderId': 456})
        mock_emit.assert_any_call('cancel_response', {'success': False, 'error': 'Order not found'})