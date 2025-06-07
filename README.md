# Binance Trading Bot

A simple trading bot for Binance Futures Testnet that supports market and limit orders.

## Features

-   Market and Limit orders support
-   Buy and Sell order sides
-   Command-line interface
-   Comprehensive logging
-   Error handling
-   Stop-Limit orders support (Bonus feature)

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your Binance Testnet API credentials:

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

3. Run the bot:

```bash
python trading_bot.py
```

## Usage

The bot provides a command-line interface with the following options:

1. Place Market Order
2. Place Limit Order
3. Place Stop-Limit Order
4. Check Account Balance
5. View Open Orders
6. Cancel Order
7. Exit

## Error Handling

The bot includes comprehensive error handling for:

-   Invalid inputs
-   API errors
-   Network issues
-   Insufficient balance
-   Invalid order parameters

## Logging

All operations are logged in `trading_bot.log` including:

-   API requests
-   Order executions
-   Errors
-   System events
