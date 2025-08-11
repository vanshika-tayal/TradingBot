import os
import pytest
from unittest.mock import patch
from trading_bot import TradingBot
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

@pytest.fixture
def trading_bot():
    if not API_KEY or not API_SECRET:
        pytest.skip("Binance API key and secret not found in .env file")
    return TradingBot(API_KEY, API_SECRET)


def test_get_account_balance_success(trading_bot):
    # Test successful retrieval of account balance
    with patch('binance.client.Client.get_account', return_value={'balances': [{'asset': 'BTC', 'free': '1.0', 'locked': '0.0'}, {'asset': 'USDT', 'free': '100.0', 'locked': '0.0'}]}):
        balances = trading_bot.get_account_balance()
        assert balances == {'BTC': {'free': 1.0, 'locked': 0.0}, 'USDT': {'free': 100.0, 'locked': 0.0}}


def test_get_account_balance_empty(trading_bot):
    # Test when no assets are found
    with patch('binance.client.Client.get_account', return_value={'balances': []}):
        balances = trading_bot.get_account_balance()
        assert balances == {}

def test_get_account_balance_api_error(trading_bot):
    # Test BinanceAPIException handling
    with patch('binance.client.Client.get_account', side_effect=BinanceAPIException(-1000, 'test error')):
        with pytest.raises(BinanceAPIException):
            trading_bot.get_account_balance()

def test_get_account_balance_exception(trading_bot):
    # Test other exceptions during account balance retrieval
    with patch('binance.client.Client.get_account', side_effect=Exception('test exception')):
        with pytest.raises(Exception):
            trading_bot.get_account_balance()


def test_get_account_balance_zero_balance(trading_bot):
    # Test scenario with zero balances
    with patch('binance.client.Client.get_account', return_value={'balances': [{'asset': 'BTC', 'free': '0.0', 'locked': '0.0'}]}):
        balances = trading_bot.get_account_balance()
        assert balances == {}

def test_get_account_balance_negative_balance(trading_bot):
    # Test scenario with negative balances (should handle gracefully)
    with patch('binance.client.Client.get_account', return_value={'balances': [{'asset': 'BTC', 'free': '-1.0', 'locked': '-0.0'}]}):
        balances = trading_bot.get_account_balance()
        assert balances == {}