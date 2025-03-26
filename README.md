# IBKR REST API

A RESTful API wrapper for Interactive Brokers (IBKR) using the IBIND library.

## What is this?

This is a simple REST API that lets you:
- Trade stocks and ETFs through Interactive Brokers
- Switch between paper trading (practice) and live trading
- Place different types of orders (market, limit, etc.)
- Check your account information and orders

Perfect for:
- Building trading applications
- Automating your trading strategies
- Learning to trade with paper money before going live

## Features

- 🔒 Secure OAuth 1.0a authentication
- 📊 Support for both paper and live trading environments
- 🔄 Real-time market data and order management
- 📈 Support for various order types (market, limit, percentage-based)
- 🎯 Position and portfolio management
- 🔍 Advanced market data queries
- 🛡️ Rate limiting and error handling
- 📝 Comprehensive logging

## Prerequisites

Before you start, make sure you have:
- Python 3.8 or higher installed
- An IBKR account (paper or live)
- Your IBKR API credentials ready
- Docker (optional, if you want to run in a container)

## Quick Start (5 minutes)

1. **Get the code:**
   ```bash
   git clone https://github.com/yourusername/ibkr-ibind-rest-api.git
   cd ibkr-ibind-rest-api
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your settings:**
   Create a `config.json` file with your IBKR credentials (see example below)

4. **Start the server:**
   ```bash
   python api.py
   ```
   Or with Docker:
   ```bash
   docker compose up -d
   ```

5. **Test it works:**
   ```bash
   curl http://localhost:5001/health
   ```
   You should see: `{"status": "ok", ...}`

## Basic Usage Examples

1. **Check your account:**
   ```bash
   curl http://localhost:5001/account
   ```

2. **Place a market order:**
   ```bash
   curl -X POST http://localhost:5001/order \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "side": "BUY",
       "quantity": 1,
       "order_type": "MKT"
     }'
   ```

3. **View your orders:**
   ```bash
   curl http://localhost:5001/orders
   ```

## Configuration

### Quick Setup (Minimal Configuration)

Create a `config.json` file in your project root with just the essential settings:

```json
{
  "paper_trading": {
    "oauth": {
      "consumer_key": "your_paper_key",
      "access_token": "your_paper_token",
      "access_token_secret": "your_paper_secret",
      "encryption_key_path": "paper_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "paper_trading_oauth_files/private_signature.pem"
    }
  }
}
```

### Full Configuration Options

For more control, you can use all available settings:

```json
{
  "name": "IBKR Configuration",
  "description": "Combined configuration for paper and live trading",
  "paper_trading": {
    "oauth": {
      "consumer_key": "your_paper_key",
      "access_token": "your_paper_token",
      "access_token_secret": "your_paper_secret",
      "encryption_key_path": "paper_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "paper_trading_oauth_files/private_signature.pem"
    },
    "api": {
      "use_paper_trading": true,
      "paper_trading_host": "https://www.ibkrstaging.com/",
      "paper_trading_api_base": "https://www.ibkrstaging.com/v1/api"
    }
  },
  "live_trading": {
    "oauth": {
      "consumer_key": "your_live_key",
      "access_token": "your_live_token",
      "access_token_secret": "your_live_secret",
      "encryption_key_path": "live_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "live_trading_oauth_files/private_signature.pem"
    },
    "api": {
      "use_paper_trading": false,
      "live_trading_host": "https://api.ibkr.com/",
      "live_trading_api_base": "https://api.ibkr.com/v1/api"
    }
  },
  "application": {
    "log_level": "INFO",
    "cache_timeout": 300,
    "auto_refresh": true
  }
}
```

### Environment Variables

You can override some settings using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `IBIND_TRADING_ENV` | Which mode to use (`paper_trading` or `live_trading`) | paper_trading |
| `IBIND_USE_OAUTH` | Enable OAuth authentication | true |
| `IBIND_ACCOUNT_ID` | Your IBKR account ID (optional) | None |

## API Reference

### Health Check
Check if the API is running:
```http
GET /health
Response: {"status": "ok", "environment": "paper_trading"}
```

### Switch Environment
Switch between paper and live trading:
```http
POST /switch-environment
Body: {"environment": "paper_trading"}  # or "live_trading"
```

### Account Information
Get your account details:
```http
GET /account
Response: {
  "status": "ok",
  "data": {
    "accounts": [...],
    "positions": [...],
    "ledger": [...]
  }
}
```

### Orders
```http
# List all orders
GET /orders

# Get a specific order
GET /order/{order_id}

# Place a new order
POST /order
Body: {
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 1,
  "order_type": "MKT"  # MKT, LMT, STP, STP_LMT
}

# Place a percentage-based limit order
POST /percentage-limit-order/{symbol}
Body: {
  "side": "BUY",
  "quantity": 1,
  "percentage": 0.5  # 0.5% below market price
}

# Cancel an order
DELETE /order/{order_id}
```

## Order Examples

### 1. View Orders

**List all orders:**
```bash
curl http://localhost:5001/orders
```

**Get a specific order:**
```bash
curl http://localhost:5001/order/1234567890
```

### 2. Market Orders

**Buy market order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 1,
    "order_type": "MKT"
  }'
```

**Sell market order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "SELL",
    "quantity": 1,
    "order_type": "MKT"
  }'
```

### 3. Limit Orders

**Buy limit order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 1,
    "order_type": "LMT",
    "price": 150.00,
    "tif": "GTC"  # Good Till Cancel
  }'
```

**Sell limit order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "SELL",
    "quantity": 1,
    "order_type": "LMT",
    "price": 170.00,
    "tif": "DAY"  # Day order
  }'
```

### 4. Stop Orders

**Stop loss order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "SELL",
    "quantity": 1,
    "order_type": "STP",
    "aux_price": 145.00  # Stop trigger price
  }'
```

**Stop limit order:**
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "SELL",
    "quantity": 1,
    "order_type": "STP_LMT",
    "price": 144.00,     # Limit price
    "aux_price": 145.00  # Stop trigger price
  }'
```

### 5. Percentage-Based Orders

**Buy below market price:**
```bash
curl -X POST http://localhost:5001/percentage-limit-order/AAPL \
  -H "Content-Type: application/json" \
  -d '{
    "side": "BUY",
    "percentage_below_market": 0.5,
    "dollar_amount": 1000
  }'
```

**Sell above market price:**
```bash
curl -X POST http://localhost:5001/percentage-limit-order/AAPL \
  -H "Content-Type: application/json" \
  -d '{
    "side": "SELL",
    "percentage_above_market": 0.5,
    "percentage_of_position": 50,
    "time_in_force": "GTC"
  }'
```

The percentage-based orders have different parameters based on the order side:

For BUY orders:
- `percentage_below_market`: Percentage below current market price to set the limit price
- `dollar_amount`: Amount in USD to buy (quantity will be calculated based on limit price)
- `time_in_force`: Optional, defaults to "GTC"

For SELL orders:
- `percentage_above_market`: Percentage above current market price to set the limit price
- `percentage_of_position`: Percentage of your current position to sell
- `time_in_force`: Optional, defaults to "GTC"

### 6. Cancel Orders

**Cancel a specific order:**
```bash
curl -X DELETE http://localhost:5001/order/1234567890
```

### Order Parameters

| Parameter | Description | Required | Values |
|-----------|-------------|----------|---------|
| `symbol` | Stock/ETF symbol | Yes | e.g., "AAPL", "SPY" |
| `side` | Buy or sell | Yes | "BUY", "SELL" |
| `quantity` | Number of shares | Yes | Any positive number |
| `order_type` | Type of order | Yes | "MKT", "LMT", "STP", "STP_LMT" |
| `price` | Limit price | For LMT orders | Any positive number |
| `aux_price` | Stop price | For STP orders | Any positive number |
| `tif` | Time in force | No | "DAY", "GTC", "IOC", "FOK" |
| `outside_rth` | Trade outside regular hours | No | true/false |

### Time in Force Options

| Value | Description |
|-------|-------------|
| `DAY` | Valid for the current trading day |
| `GTC` | Good Till Canceled |
| `IOC` | Immediate or Cancel |
| `FOK` | Fill or Kill |

## Common Issues & Solutions

### "Cannot connect to server"
1. Check if the server is running: `curl http://localhost:5001/health`
2. Make sure you're using the right port (5001)
3. If using Docker, check container status: `docker compose ps`

### "Authentication failed"
1. Verify your OAuth credentials in `config.json`
2. Check that your OAuth key files exist and are readable
3. Make sure you're in the right environment (paper/live)

### "Order rejected"
1. Check your account has enough funds
2. Verify market hours (most US stocks trade 9:30 AM - 4:00 PM ET)
3. For limit orders, check if your price is reasonable

## Security Checklist

✅ **Before going live:**
1. Test thoroughly in paper trading mode first
2. Keep your OAuth credentials secure
3. Use environment variables for sensitive data
4. Never commit credentials to git
5. Set up proper monitoring and alerts

## Getting Help

Need help? Here's what to do:

1. **Check the docs:**
   - Read this README thoroughly
   - Look for similar issues in our issue tracker
   - Check IBKR's [official documentation](https://www.interactivebrokers.com/api/doc.html)

2. **Debug your issue:**
   - Check the API logs (default location: `./logs/api.log`)
   - Try the request in paper trading mode first
   - Use `curl` to test endpoints directly

3. **Get support:**
   - [Open an issue](https://github.com/yourusername/ibkr-ibind-rest-api/issues/new)
   - Include:
     - What you're trying to do
     - What you've tried
     - Any error messages
     - Relevant log snippets

## Contributing

Want to help improve this API? Great! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the documentation
2. Review existing issues
3. Create a new issue if needed
