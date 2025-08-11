import pytest
import os
from dotenv import load_dotenv
from trading_bot import TradingBot
from binance.exceptions import BinanceAPIException

# Load environment variables from .env file
load_dotenv()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

#Skip tests if API keys are not found
pytestmark = pytest.mark.skipif(not BINANCE_API_KEY or not BINANCE_API_SECRET, reason="BINANCE_API_KEY or BINANCE_API_SECRET not found in .env")


@pytest.fixture
def trading_bot():
    """Fixture to create a TradingBot instance."""
    bot = TradingBot(BINANCE_API_KEY, BINANCE_API_SECRET)
    yield bot
    #Teardown - Not needed here as Binance client manages its own resources


def test_get_account_balance(trading_bot):
    """Test retrieving account balances."""
    try:
        balances = trading_bot.get_account_balance()
        assert isinstance(balances, dict)
        assert len(balances) > 0  #Expect at least one asset with balance
        for asset, balance in balances.items():
            assert isinstance(asset, str)
            assert isinstance(balance['free'], float)
            assert isinstance(balance['locked'], float)
    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")


def test_place_market_order(trading_bot):
    """Test placing a market order (using small quantity on a testnet)."""
    #This test is designed to run on testnet and will only use a tiny amount
    symbol = "BTCUSDT" #Replace with a suitable testnet pair
    side = "BUY"
    quantity = 0.000001 # Extremely small quantity for testing
    try:
        order = trading_bot.place_market_order(symbol, side, quantity)
        assert isinstance(order, dict)
        assert order['status'] == 'FILLED' #Expect order to be filled immediately on testnet
        #Add more assertions as needed based on the order details
        #Consider adding cancel_order after this for cleanup
    except BinanceAPIException as e:
        if e.code == -1100 or e.code == -2010: #Ignore insufficient balance and order not found.
            pytest.skip(f"Binance API Exception (likely insufficient balance): {e}")
        else:
            pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")

def test_place_limit_order(trading_bot):
    """Test placing a limit order (will not be filled)."""
    symbol = "BTCUSDT" #Replace with a suitable testnet pair
    side = "BUY"
    quantity = 0.000001
    price = 100000 #Set an unrealistic price to avoid accidental execution
    try:
        order = trading_bot.place_limit_order(symbol,side,quantity,price)
        assert isinstance(order,dict)
        assert order['status'] == 'NEW' #Expect the order to be open
        #Add more assertions, consider cancelling the order as cleanup
    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")

def test_place_stop_limit_order(trading_bot):
    """Test placing a stop-limit order (will not be filled)."""
    symbol = "BTCUSDT" #Replace with a suitable testnet pair
    side = "BUY"
    quantity = 0.000001
    price = 100000
    stop_price = 100001
    try:
        order = trading_bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)
        assert isinstance(order,dict)
        assert order['status'] == 'NEW' #Expect the order to be open
        #Add more assertions, consider cancelling the order as cleanup
    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")

def test_get_open_orders(trading_bot):
    """Test retrieving open orders."""
    try:
        orders = trading_bot.get_open_orders()
        assert isinstance(orders, list)
        #Further assertions depending on expected open orders
    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")

def test_cancel_order(trading_bot):
    """Test cancelling an order (requires placing an order first)."""
    #This test requires a valid order ID, which would need to be obtained beforehand
    #Use a previous test's created order ID or create one here, but ensure proper cleanup.
    pytest.skip("Requires a pre-existing open order to test cancellation")