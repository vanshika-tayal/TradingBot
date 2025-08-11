import os
import pytest
from dotenv import load_dotenv
from trading_bot import TradingBot
from binance.exceptions import BinanceAPIException

load_dotenv()

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

@pytest.fixture
def trading_bot():
    if not API_KEY or not API_SECRET:
        pytest.skip("Binance API keys not found in .env file")
    bot = TradingBot(API_KEY, API_SECRET)
    yield bot
    # Add teardown if needed, e.g., closing connections

def test_get_account_balance(trading_bot):
    try:
        balances = trading_bot.get_account_balance()
        assert isinstance(balances, dict)
        assert len(balances) > 0  # Expect at least one asset with a balance
        for asset, balance in balances.items():
            assert isinstance(asset, str)
            assert isinstance(balance['free'], float)
            assert isinstance(balance['locked'], float)
            assert balance['free'] >= 0
            assert balance['locked'] >= 0

    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")


def test_place_market_order(trading_bot):
    # This test requires a testnet account with sufficient funds
    # Replace with a valid symbol and adjust quantity as needed
    symbol = "BTCUSDT"
    side = "BUY"
    quantity = 0.0001 #Use a very small quantity for testnet

    try:
        order = trading_bot.place_market_order(symbol, side, quantity)
        assert isinstance(order, dict)
        assert order['status'] == 'FILLED' # Or another appropriate status if not fully filled
        assert order['symbol'] == symbol
        assert order['side'] == side
        assert float(order['origQty']) == quantity

    except BinanceAPIException as e:
        if "Insufficient" in str(e):
            pytest.skip("Insufficient funds for test")  #Skip if insufficient balance
        else:
            pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")
    finally:
        #Attempt to cancel the order, if placed.  This helps ensure testnet account isn't affected long term
        open_orders = trading_bot.get_open_orders(symbol)
        for order in open_orders:
            trading_bot.cancel_order(symbol, order['orderId'])


def test_place_limit_order(trading_bot):
    #Similar to test_place_market_order, needs testnet account and adjustments
    symbol = "BTCUSDT"
    side = "BUY"
    quantity = 0.0001
    price = 28000 # Example price, adjust as needed

    try:
        order = trading_bot.place_limit_order(symbol, side, quantity, price)
        assert isinstance(order, dict)
        assert order['status'] in ['NEW', 'PARTIALLY_FILLED'] #Expect either depending on market conditions
        assert order['symbol'] == symbol
        assert order['side'] == side
        assert float(order['origQty']) == quantity
        assert float(order['price']) == price

    except BinanceAPIException as e:
        if "Insufficient" in str(e):
            pytest.skip("Insufficient funds for test")
        else:
            pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")
    finally:
        open_orders = trading_bot.get_open_orders(symbol)
        for order in open_orders:
            trading_bot.cancel_order(symbol, order['orderId'])


def test_place_stop_limit_order(trading_bot):
    # Requires testnet account, adjust parameters as needed
    symbol = "BTCUSDT"
    side = "BUY"
    quantity = 0.0001
    price = 28000
    stop_price = 27500

    try:
        order = trading_bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)
        assert isinstance(order, dict)
        assert order['status'] == 'NEW' #Likely not filled immediately
        assert order['symbol'] == symbol
        assert order['side'] == side
        assert float(order['origQty']) == quantity
        assert float(order['price']) == price
        assert float(order['stopPrice']) == stop_price

    except BinanceAPIException as e:
        if "Insufficient" in str(e):
            pytest.skip("Insufficient funds for test")
        else:
            pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")
    finally:
        open_orders = trading_bot.get_open_orders(symbol)
        for order in open_orders:
            trading_bot.cancel_order(symbol, order['orderId'])


def test_get_open_orders(trading_bot):
    try:
        orders = trading_bot.get_open_orders()
        assert isinstance(orders, list)
        #Test with specific symbol
        orders_btc = trading_bot.get_open_orders("BTCUSDT")
        assert isinstance(orders_btc, list)
    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")


def test_cancel_order(trading_bot):
    #Requires placing an order first -  needs testnet acccount and adjustments.  Use a previous test to place an order
    symbol = "BTCUSDT"
    try:
        orders = trading_bot.get_open_orders(symbol)
        if orders:
            order_to_cancel = orders[0]  #Cancel the first open order found
            result = trading_bot.cancel_order(symbol, order_to_cancel['orderId'])
            assert isinstance(result, dict)
            assert result['status'] == 'CANCELED' # Or a similar status indicating cancellation

        else:
            pytest.skip("No open orders to cancel")

    except BinanceAPIException as e:
        pytest.fail(f"Binance API Exception: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}")