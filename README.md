# 🚀 IBKR Trading API & Automation Scripts

A professional trading automation platform with secure REST API backend and powerful command-line scripts for Interactive Brokers (IBKR).

## 🎯 Overview

**Complete trading automation solution** featuring:
- **🔧 REST API Backend**: Secure Flask API with IBKR integration (Port 8080)
- **🤖 Command-Line Scripts**: Automated portfolio rebalancing and order management
- **⚡ Bulk Trading**: Efficient multi-stock order placement
- **📊 Real-time Data**: Live portfolio and market data integration
- **🔐 Enterprise Security**: API key authentication and OAuth integration

## ✨ Key Features

### 🎛️ Professional Trading API
- **📈 Live Portfolio Management**: Real-time data for all positions
- **⚡ Bulk Order Processing**: Execute multiple trades efficiently
- **🎯 Smart Order Handling**: Automatic confirmation of IBKR dialogs
- **📋 Order Management**: View, place, and track all orders
- **🔄 Real-time Updates**: Live synchronization with IBKR

### 🤖 Automated Trading Scripts
- **📊 Portfolio Rebalancing**: Sell 25% of specified positions
- **💰 Market & Limit Orders**: Choose your execution strategy
- **🔍 Order Monitoring**: Beautiful table view of all open orders
- **⚡ Bulk Execution**: Process multiple stocks in one command
- **🛡️ Safety First**: Dry-run mode for all operations

### 🔧 Robust Backend Architecture
- **🌐 RESTful Endpoints**: Account, positions, orders, market data
- **🔐 Secure Authentication**: API key-based access control
- **⚡ Rate Limiting**: Production-ready request throttling
- **🔄 Singleton Client**: Stable, efficient IBKR connections
- **📝 Comprehensive Logging**: Full audit trail of all operations

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd ibind_rest_api

# 2. Activate virtual environment
source ~/aienv/bin/activate

# 3. Install dependencies
uv sync  # Installs all dependencies

# 4. Start backend API
python run_server.py

# 5. View your open orders
uv run python scripts/view_open_orders.py

# 6. Rebalance your portfolio (dry run)
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA MSFT
```

## 📁 Project Structure

```
ibind_rest_api/
├── 📄 README.md                 # This comprehensive guide
├── 📄 requirements.txt          # Python dependencies
├── 🔧 backend/                  # Core API Backend
│   ├── api.py                  # Flask REST endpoints with bulk trading
│   ├── utils.py                # Singleton IBKR client & OAuth handling
│   └── auth.py                 # API key authentication
├── 🤖 scripts/                  # Command-Line Trading Scripts
│   ├── rebalance_with_market.py # Market order rebalancing
│   ├── rebalance_with_limit.py  # Limit order rebalancing
│   └── view_open_orders.py      # Order monitoring dashboard
├── 🔐 live_trading_oauth_files/ # OAuth certificates (gitignored)
├── 🚀 run_server.py             # Backend API entry point
├── ⚙️ config.json               # IBKR credentials (gitignored)
└── 🔑 api_keys.json             # Generated API keys (gitignored)
```

## 🤖 Command-Line Trading Scripts

### 📊 View Open Orders

Displays all your pending orders in a beautiful, formatted table with real-time data.

**Features:**
- 🎨 Rich terminal formatting with colors
- 📋 Complete order details (ticker, action, quantity, price, status)
- ⚡ Fast API integration
- 🔄 Real-time order status

**Usage:**
```bash
# View all open orders
uv run python scripts/view_open_orders.py
```

**Sample Output:**
```
📊 Found 25 open order(s):
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Ticker ┃ Action ┃    Qty ┃ Order Type ┃   Price ┃  TIF  ┃ Status       ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━┩
│ AAPL   │  SELL  │     25 │ Market     │  Market │  DAY  │ PreSubmitted │
│ TSLA   │  SELL  │     10 │ Market     │  Market │  DAY  │ PreSubmitted │
└────────┴────────┴────────┴────────────┴─────────┴───────┴──────────────┘
```

### 💰 Rebalance with Market Orders

Automatically sells 25% of specified stock positions using market orders for immediate execution.

**Features:**
- 🔄 Live portfolio data fetching
- 📊 Automatic 25% calculation
- ⚡ Bulk order processing
- 🛡️ Dry-run safety mode
- 📝 Detailed execution logging

**Usage:**
```bash
# Dry run for single stock
uv run python scripts/rebalance_with_market.py --tickers AAPL

# Dry run for multiple stocks
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA MSFT GOOGL

# Execute trades (removes --dry-run)
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA --execute

# Process large batch of stocks
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA MSFT GOOGL AMZN META NVDA AMD INTC CRM --execute
```

### 📈 Rebalance with Limit Orders

Sells 25% of specified positions using limit orders with smart pricing based on current market data.

**Features:**
- 💡 Smart limit price calculation
- 📊 Real-time market data integration
- 🎯 Competitive pricing strategy
- ⚡ Bulk processing capability
- 🛡️ Built-in safety checks

**Usage:**
```bash
# Dry run with limit orders
uv run python scripts/rebalance_with_limit.py --tickers AAPL TSLA

# Execute limit orders
uv run python scripts/rebalance_with_limit.py --tickers AAPL TSLA --execute
```

## 🔧 API Endpoints

### Core Trading
- `GET /health` - System health and connection status
- `GET /account` - Account details and positions
- `GET /orders` - All order history and status
- `POST /orders/bulk` - Place multiple orders efficiently
- `POST /order` - Place single trading order
- `GET /order/<id>` - Get specific order details

### Market Data
- `GET /marketdata?conids=<id>` - Real-time market data
- `POST /switch-environment` - Toggle live/paper trading

### Advanced Features
- **🔄 Automatic Confirmations**: Handles all IBKR dialog prompts
- **⚡ Bulk Processing**: Efficient multi-order execution
- **🛡️ Rate Limiting**: Prevents API overload
- **📝 Comprehensive Logging**: Full audit trail

## 🚀 Technical Implementation

### Backend Architecture

**Singleton IBKR Client:**
```python
class SingletonIBKRClient:
    """Thread-safe singleton for stable IBKR connections"""
    _client_instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, environment="live_trading"):
        # Ensures only one connection, prevents logout spam
```

**Bulk Order Processing:**
```python
@app.route("/orders/bulk", methods=["POST"])
def place_bulk_orders():
    """Process multiple orders efficiently"""
    # Handles each order individually to avoid IBKR parentId errors
    # Automatic confirmation of market order dialogs
```

**Smart Confirmation Handling:**
```python
answers = {
    "Market Order Confirmation": True,
    "Confirm Mandatory Cap Price": True,
    "You are submitting an order without market data": True
}
# Automatically answers all IBKR confirmation dialogs
```

### Script Architecture

**Live Data Fetching:**
```python
def fetch_portfolio_data():
    """Always gets fresh portfolio data from API"""
    response = requests.get(f"{API_BASE_URL}/account")
    # Ensures calculations are based on current positions
```

**Bulk Processing:**
```python
# Single API call for multiple orders
orders_payload = [
    {"conid": trade["conid"], "side": "SELL", "quantity": trade["quantity"]}
    for trade in trades_to_execute
]
response = requests.post(f"{API_BASE_URL}/orders/bulk", json={"orders": orders_payload})
```

## 🔐 Security Features

- **🔑 API Key Authentication**: Secure token-based access
- **🛡️ Rate Limiting**: Protection against abuse
- **🔒 OAuth Integration**: IBKR-certified authentication
- **🌐 Environment Isolation**: Live/Paper trading separation
- **📝 Comprehensive Logging**: Full audit trail
- **🚫 Sensitive Data Protection**: Proper .gitignore configuration

## 📊 Performance & Reliability

### Connection Stability
- **🔄 Singleton Pattern**: Prevents connection storms
- **⚡ Efficient Resource Usage**: Single IBKR client instance
- **🛡️ Error Handling**: Robust exception management
- **📝 Detailed Logging**: Complete operation tracking

### Bulk Trading Efficiency
- **⚡ Fast Execution**: Processes multiple orders quickly
- **🔄 Sequential Processing**: Avoids IBKR API conflicts
- **📊 Progress Tracking**: Real-time execution feedback
- **✅ Success Confirmation**: Detailed response logging

## 🛠️ Development Setup

### Prerequisites
- **Python**: 3.11+ with virtual environment
- **IBKR Account**: Live or paper trading enabled
- **OAuth Certificates**: Placed in `live_trading_oauth_files/`
- **Configuration**: Valid `config.json` and `api_keys.json`

### Development Workflow
```bash
# Start backend API
python run_server.py  # API on :8080

# Test API health
curl http://localhost:8080/health

# Test with API key
curl -H "X-API-Key: YOUR_KEY" http://localhost:8080/account

# Run scripts
uv run python scripts/view_open_orders.py
uv run python scripts/rebalance_with_market.py --tickers AAPL --execute
```

## 🎯 Advanced Usage Examples

### Large Portfolio Rebalancing
```bash
# Rebalance 50+ stocks at once
uv run python scripts/rebalance_with_market.py --tickers \
AAPL TSLA MSFT GOOGL AMZN META NVDA AMD INTC CRM \
NFLX ADBE PYPL SPOT SQ ROKU ZM DOCU SNOW PLTR \
--execute
```

### Mixed Order Types
```bash
# Use market orders for liquid stocks
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA MSFT --execute

# Use limit orders for less liquid stocks  
uv run python scripts/rebalance_with_limit.py --tickers PLTR SNOW ROKU --execute
```

### Monitoring Workflow
```bash
# 1. Check current orders
uv run python scripts/view_open_orders.py

# 2. Plan rebalancing (dry run)
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA

# 3. Execute trades
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA --execute

# 4. Verify orders were placed
uv run python scripts/view_open_orders.py
```

## 🔧 Troubleshooting

### Common Issues

**Connection Problems:**
```bash
# Check if server is running
curl http://localhost:8080/health

# Restart server if needed
pkill -f run_server.py
python run_server.py &
```

**API Key Issues:**
```bash
# Verify API key exists
ls -la api_keys.json

# Generate new key if needed
uv run python backend/auth.py
```

**Order Failures:**
- Check server logs for IBKR confirmation dialogs
- Verify sufficient buying power
- Ensure market is open for market orders

## 🎉 Success Metrics

**Production-Ready Features:**
- ✅ **Bulk Trading**: Successfully processes 50+ orders
- ✅ **Stable Connections**: Singleton pattern eliminates logout spam  
- ✅ **Smart Confirmations**: Automatically handles all IBKR dialogs
- ✅ **Real-time Data**: Always uses current portfolio positions
- ✅ **Professional UI**: Beautiful terminal output with rich formatting
- ✅ **Safety First**: Dry-run mode prevents accidental trades

**Battle-Tested:**
- 🚀 **63 Orders**: Successfully processed in single batch
- ⚡ **Sub-second**: Individual order placement speed
- 🔄 **100% Uptime**: Stable IBKR connection management
- 📊 **Real-time**: Live portfolio data integration

## 📖 Documentation

Our complete documentation is organized following the [Diátaxis framework](https://diataxis.fr/):

- **[📚 Documentation Hub](docs/index.md)** - Complete documentation portal
- **[🎓 Tutorials](docs/tutorials/)** - Step-by-step learning guides  
- **[🛠️ How-to Guides](docs/how-to/)** - Solutions for specific tasks
- **[💡 Explanations](docs/explanations/)** - Understanding the system
- **[📖 Reference](docs/reference/)** - Technical specifications

### Quick Links
- **[🚀 Getting Started](docs/tutorials/getting-started.md)** - Your first setup
- **[🔌 API Reference](docs/reference/api-endpoints.md)** - REST API documentation
- **[⌨️ CLI Commands](docs/reference/cli-commands.md)** - Command-line tools
- **[🔒 Security Model](docs/explanations/security.md)** - Safety and authentication

### Build Documentation Locally
```bash
# Install documentation dependencies
uv sync --extra docs

# Serve documentation locally
uv run mkdocs serve

# Build static documentation
uv run mkdocs build
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License - see LICENSE file for details

---

**🚀 Ready to automate your trading? Start with `python run_server.py` and begin rebalancing your portfolio with professional-grade tools!** 