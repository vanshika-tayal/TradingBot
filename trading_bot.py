import os
import logging
from datetime import datetime
from typing import Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

console = Console()

class TradingBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize the trading bot with API credentials."""
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            logging.info("Successfully initialized Binance client")
            # Use testnet base URLs
            self.client.API_URL = 'https://testnet.binance.vision/api'
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
        except Exception as e:
            logging.error(f"Failed to initialize Binance client: {str(e)}")
            raise

    def get_account_balance(self) -> Dict:
        """Get account balance for all assets."""
        try:
            balances = self.client.get_account()['balances']
            logging.info("Successfully retrieved account balance")
            return {
                balance['asset']: {
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                }
                for balance in balances
                if float(balance['free']) > 0 or float(balance['locked']) > 0
            }
        except BinanceAPIException as e:
            logging.error(f"Failed to get account balance: {str(e)}")
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """Place a market order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logging.info(f"Successfully placed market order: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Failed to place market order: {str(e)}")
            raise

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Place a limit order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            logging.info(f"Successfully placed limit order: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Failed to place limit order: {str(e)}")
            raise

    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                             price: float, stop_price: float) -> Dict:
        """Place a stop-limit order."""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price,
                stopPrice=stop_price
            )
            logging.info(f"Successfully placed stop-limit order: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Failed to place stop-limit order: {str(e)}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Get all open orders for a symbol."""
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            logging.info(f"Successfully retrieved open orders for {symbol if symbol else 'all symbols'}")
            return orders
        except BinanceAPIException as e:
            logging.error(f"Failed to get open orders: {str(e)}")
            raise

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an open order."""
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logging.info(f"Successfully cancelled order {order_id}")
            return result
        except BinanceAPIException as e:
            logging.error(f"Failed to cancel order: {str(e)}")
            raise

def display_menu():
    """Display the main menu."""
    table = Table(title="Trading Bot Menu")
    table.add_column("Option", style="cyan")
    table.add_column("Description", style="green")
    
    options = [
        ("1", "Place Market Order"),
        ("2", "Place Limit Order"),
        ("3", "Place Stop-Limit Order"),
        ("4", "Check Account Balance"),
        ("5", "View Open Orders"),
        ("6", "Cancel Order"),
        ("7", "Exit")
    ]
    
    for option, description in options:
        table.add_row(option, description)
    
    console.print(table)

def get_user_input(prompt: str, valid_options: Optional[list] = None) -> str:
    """Get and validate user input."""
    while True:
        value = input(prompt).strip().upper()
        if valid_options is None or value in valid_options:
            return value
        console.print(f"Invalid input. Please choose from {valid_options}", style="red")

def main():
    """Main function to run the trading bot."""
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        console.print("Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env file", style="red")
        return

    try:
        bot = TradingBot(api_key, api_secret)
        console.print("Successfully connected to Binance Testnet!", style="green")
    except Exception as e:
        console.print(f"Failed to initialize bot: {str(e)}", style="red")
        return

    while True:
        display_menu()
        choice = get_user_input("Enter your choice (1-7): ", [str(i) for i in range(1, 8)])
        
        try:
            if choice == '1':  # Market Order
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY/SELL): ", ['BUY', 'SELL'])
                quantity = float(input("Enter quantity: "))
                
                order = bot.place_market_order(symbol, side, quantity)
                console.print("Market order placed successfully!", style="green")
                console.print(order)

            elif choice == '2':  # Limit Order
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY/SELL): ", ['BUY', 'SELL'])
                quantity = float(input("Enter quantity: "))
                price = float(input("Enter price: "))
                
                order = bot.place_limit_order(symbol, side, quantity, price)
                console.print("Limit order placed successfully!", style="green")
                console.print(order)

            elif choice == '3':  # Stop-Limit Order
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY/SELL): ", ['BUY', 'SELL'])
                quantity = float(input("Enter quantity: "))
                price = float(input("Enter limit price: "))
                stop_price = float(input("Enter stop price: "))
                
                order = bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)
                console.print("Stop-limit order placed successfully!", style="green")
                console.print(order)

            elif choice == '4':  # Check Balance
                balances = bot.get_account_balance()
                table = Table(title="Account Balances")
                table.add_column("Asset", style="cyan")
                table.add_column("Free", style="green")
                table.add_column("Locked", style="yellow")
                
                for asset, balance in balances.items():
                    table.add_row(asset, str(balance['free']), str(balance['locked']))
                
                console.print(table)

            elif choice == '5':  # View Open Orders
                symbol = input("Enter symbol (or press Enter for all symbols): ").strip().upper()
                symbol = symbol if symbol else None
                
                orders = bot.get_open_orders(symbol)
                if not orders:
                    console.print("No open orders found.", style="yellow")
                else:
                    table = Table(title="Open Orders")
                    table.add_column("Symbol", style="cyan")
                    table.add_column("Order ID", style="green")
                    table.add_column("Type", style="yellow")
                    table.add_column("Side", style="magenta")
                    table.add_column("Price", style="blue")
                    table.add_column("Quantity", style="white")
                    
                    for order in orders:
                        table.add_row(
                            order['symbol'],
                            str(order['orderId']),
                            order['type'],
                            order['side'],
                            str(order['price']),
                            str(order['origQty'])
                        )
                    
                    console.print(table)

            elif choice == '6':  # Cancel Order
                symbol = get_user_input("Enter symbol: ")
                order_id = int(input("Enter order ID: "))
                
                result = bot.cancel_order(symbol, order_id)
                console.print("Order cancelled successfully!", style="green")
                console.print(result)

            elif choice == '7':  # Exit
                console.print("Thank you for using the trading bot!", style="green")
                break

        except BinanceAPIException as e:
            console.print(f"Binance API Error: {str(e)}", style="red")
        except ValueError as e:
            console.print(f"Invalid input: {str(e)}", style="red")
        except Exception as e:
            console.print(f"An error occurred: {str(e)}", style="red")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 