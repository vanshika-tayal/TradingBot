import os
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Binance client
try:
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=True
    )
    client.API_URL = 'https://testnet.binance.vision/api'
    logging.info("Successfully initialized Binance client")
except Exception as e:
    logging.error(f"Failed to initialize Binance client: {str(e)}")
    raise

def format_number(number, decimals=8):
    """Format number to specified decimal places."""
    return f"{float(number):.{decimals}f}"

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/symbols')
def get_symbols():
    """Get available trading symbols."""
    try:
        exchange_info = client.get_exchange_info()
        symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]
        return jsonify(symbols)
    except Exception as e:
        logging.error(f"Failed to get symbols: {str(e)}")
        return jsonify([])

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logging.info("Client connected")
    emit('balance_update', get_account_balance())
    emit('open_orders_update', get_open_orders())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logging.info("Client disconnected")

@socketio.on('get_balance')
def handle_get_balance():
    """Handle balance request."""
    emit('balance_update', get_account_balance())

@socketio.on('get_open_orders')
def handle_get_open_orders():
    """Handle open orders request."""
    orders = get_open_orders()
    emit('open_orders_update', orders)

@socketio.on('place_order')
def handle_place_order(data):
    """Handle order placement request."""
    try:
        order_params = {
            'symbol': data['symbol'],
            'side': data['side'],
            'type': data['type'],
            'quantity': format_number(data['quantity'])
        }

        if data['type'] in ['LIMIT', 'STOP_LIMIT']:
            order_params['timeInForce'] = 'GTC'
            order_params['price'] = format_number(data['price'])

        if data['type'] == 'STOP_LIMIT':
            order_params['stopPrice'] = format_number(data['stopPrice'])

        # Place the order
        order = client.create_order(**order_params)
        logging.info(f"Successfully placed order: {order}")
        
        # For market orders, get the filled order details
        if data['type'] == 'MARKET':
            order = client.get_order(
                symbol=data['symbol'],
                orderId=order['orderId']
            )

        # Format the response
        formatted_order = {
            'symbol': order['symbol'],
            'orderId': order['orderId'],
            'type': order['type'],
            'side': order['side'],
            'price': format_number(order['price']) if 'price' in order else format_number(order.get('cummulativeQuoteQty', '0')),
            'origQty': format_number(order['origQty']),
            'executedQty': format_number(order.get('executedQty', '0')),
            'status': order['status'],
            'time': datetime.fromtimestamp(order['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        emit('order_response', {'success': True, 'order': formatted_order})
        
        # Update client with new data
        emit('balance_update', get_account_balance())
        
        # For market orders, also send recent trades
        if data['type'] == 'MARKET':
            emit('recent_trades_update', get_recent_trades(data['symbol']))
        else:
            emit('open_orders_update', get_open_orders())

    except BinanceAPIException as e:
        logging.error(f"Failed to place order: {str(e)}")
        emit('order_response', {'success': False, 'error': str(e)})
    except Exception as e:
        logging.error(f"Error placing order: {str(e)}")
        emit('order_response', {'success': False, 'error': 'An unexpected error occurred'})

@socketio.on('cancel_order')
def handle_cancel_order(data):
    """Handle order cancellation request."""
    try:
        result = client.cancel_order(
            symbol=data['symbol'],
            orderId=data['orderId']
        )
        logging.info(f"Successfully cancelled order {data['orderId']}")
        emit('cancel_response', {'success': True})
        
        # Update client with new data
        emit('balance_update', get_account_balance())
        emit('open_orders_update', get_open_orders())

    except BinanceAPIException as e:
        logging.error(f"Failed to cancel order: {str(e)}")
        emit('cancel_response', {'success': False, 'error': str(e)})
    except Exception as e:
        logging.error(f"Error cancelling order: {str(e)}")
        emit('cancel_response', {'success': False, 'error': 'An unexpected error occurred'})

def get_account_balance():
    """Get account balance for all assets."""
    try:
        balances = client.get_account()['balances']
        return {
            balance['asset']: {
                'free': format_number(balance['free']),
                'locked': format_number(balance['locked'])
            }
            for balance in balances
            if float(balance['free']) > 0 or float(balance['locked']) > 0
        }
    except Exception as e:
        logging.error(f"Failed to get account balance: {str(e)}")
        return {}

def get_open_orders(symbol=None):
    """Get all open orders for a symbol."""
    try:
        orders = client.get_open_orders(symbol=symbol)
        return [{
            'symbol': order['symbol'],
            'orderId': order['orderId'],
            'type': order['type'],
            'side': order['side'],
            'price': format_number(order['price']),
            'origQty': format_number(order['origQty']),
            'executedQty': format_number(order.get('executedQty', '0')),
            'status': order['status'],
            'time': datetime.fromtimestamp(order['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        } for order in orders]
    except Exception as e:
        logging.error(f"Failed to get open orders: {str(e)}")
        return []

def get_recent_trades(symbol):
    """Get recent trades for a symbol."""
    try:
        trades = client.get_my_trades(symbol=symbol, limit=10)
        return [{
            'symbol': trade['symbol'],
            'orderId': trade['orderId'],
            'price': format_number(trade['price']),
            'qty': format_number(trade['qty']),
            'quoteQty': format_number(trade['quoteQty']),
            'commission': format_number(trade['commission']),
            'commissionAsset': trade['commissionAsset'],
            'time': datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'isBuyer': trade['isBuyer'],
            'isMaker': trade['isMaker']
        } for trade in reversed(trades)]
    except Exception as e:
        logging.error(f"Failed to get recent trades: {str(e)}")
        return []

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8000) 