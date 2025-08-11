import os
import pytest
from app import app, client, get_account_balance, get_open_orders, get_recent_trades, handle_place_order
from unittest.mock import patch, MagicMock
from binance.exceptions import BinanceAPIException
from flask_socketio import SocketIO

# Mocking environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "test_api_key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test_api_secret")

# Mocking Binance client
@pytest.fixture
def mock_binance_client():
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def socketio_client(request):
    test_client = app.test_client()
    socketio = SocketIO(app)
    def teardown():
        socketio.disconnect()

    request.addfinalizer(teardown)
    return test_client, socketio


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    with pytest.raises(Exception) as e:
        app.config['SECRET_KEY'] = os.urandom(24)
        socketio = SocketIO(app, cors_allowed_origins="*")
    assert "Failed to initialize Binance client" in str(e.value)


def test_missing_api_secret(monkeypatch):
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)
    with pytest.raises(Exception) as e:
        app.config['SECRET_KEY'] = os.urandom(24)
        socketio = SocketIO(app, cors_allowed_origins="*")
    assert "Failed to initialize Binance client" in str(e.value)


def test_invalid_api_key(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "invalid_api_key")
    with pytest.raises(BinanceAPIException) as e:
        app.config['SECRET_KEY'] = os.urandom(24)
        socketio = SocketIO(app, cors_allowed_origins="*")
    assert "Failed to initialize Binance client" in str(e.value)


def test_invalid_api_secret(monkeypatch):
    monkeypatch.setenv("BINANCE_API_SECRET", "invalid_api_secret")
    with pytest.raises(BinanceAPIException) as e:
        app.config['SECRET_KEY'] = os.urandom(24)
        socketio = SocketIO(app, cors_allowed_origins="*")
    assert "Failed to initialize Binance client" in str(e.value)


def test_get_account_balance(mock_binance_client):
    mock_binance_client.get_account.return_value = {'balances': [{'asset': 'BTC', 'free': '1.0', 'locked': '0.0'}, {'asset': 'ETH', 'free': '0.0', 'locked': '0.1'}]}
    balances = get_account_balance()
    assert balances == {'BTC': {'free': '1.00000000', 'locked': '0.00000000'}, 'ETH': {'free': '0.00000000', 'locked': '0.10000000'}}


def test_get_open_orders(mock_binance_client):
    mock_binance_client.get_open_orders.return_value = [{'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'origQty': '1', 'executedQty': '0', 'status': 'NEW'}]
    orders = get_open_orders()
    assert len(orders) == 1
    assert orders[0]['symbol'] == 'BTCUSDT'


def test_get_recent_trades(mock_binance_client):
    mock_binance_client.get_my_trades.return_value = [{'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'qty': '1', 'commission': '0.001', 'commissionAsset': 'BTC', 'time': 1678886400000}]
    trades = get_recent_trades('BTCUSDT')
    assert len(trades) == 1
    assert trades[0]['symbol'] == 'BTCUSDT'


@patch('app.client.create_order')
def test_handle_place_order_success(mock_create_order, mock_binance_client, socketio_client):
    test_client, socketio = socketio_client
    mock_create_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'origQty': '1', 'executedQty': '1', 'status': 'FILLED', 'time': 1678886400000}
    mock_binance_client.get_order.return_value = {'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'origQty': '1', 'executedQty': '1', 'status': 'FILLED', 'time': 1678886400000}
    mock_binance_client.get_my_trades.return_value = [{'symbol': 'BTCUSDT', 'orderId': 123, 'price': '10000', 'qty': '1', 'commission': '0.001', 'commissionAsset': 'BTC', 'time': 1678886400000}]
    response = test_client.emit('place_order', {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '1'})
    assert response == {'success':True}



@patch('app.client.create_order')
def test_handle_place_order_failure(mock_create_order, mock_binance_client, socketio_client):
    test_client, socketio = socketio_client
    mock_create_order.side_effect = BinanceAPIException(-1013,'Invalid quantity')
    response = test_client.emit('place_order', {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '1'})
    assert response == {'success': False}