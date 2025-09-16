# 🚀 IBKR Trading API

Minimal REST API for Interactive Brokers trading automation. Designed for local automation, cron jobs, and algorithmic trading.

## ⚡ Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Start API server
uv run python run_server.py
```

**API Server**: http://127.0.0.1:8080 (localhost only)

## 🔧 Local Automation Setup

No authentication required - designed for trusted local environment:

```bash
# Check system health
curl http://127.0.0.1:8080/health

# Get account info
curl http://127.0.0.1:8080/account

# Place order by symbol
curl -X POST http://127.0.0.1:8080/order/symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"BUY","quantity":1,"order_type":"MKT"}'
```

## 🎯 Core Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System status |
| `GET /account` | Account info + positions |
| `GET /positions?limit=200` | Portfolio positions |
| `GET /resolve/{symbol}` | Symbol → Contract ID |
| `POST /order` | Place orders (requires contract ID) |
| `POST /order/symbol` | Place orders by symbol (auto-resolves) |
| `POST /percentage-order/{symbol}` | Percentage-based position sizing |
| `GET /orders` | Get all current orders |

## 📱 Features

- **Zero authentication** - trusted local environment
- **Minimal dependencies** - no CORS, rate limiting, or UI bloat  
- **Automation-ready** - perfect for cron jobs and scripts
- **Symbol resolution** - trade by ticker without manual lookups
- **Percentage orders** - position sizing based on account value
- **Extended hours trading** - algorithmic trading outside market hours

## 🛠️ Configuration

1. **OAuth Setup**: Add IBKR OAuth files to `live_trading_oauth_files/`
2. **Environment**: Set `IBIND_TRADING_ENV=live_trading`
3. **Port**: Set `PORT=8080` (optional)

## 📦 Dependencies

- Python 3.13+
- Flask (minimal setup)
- ibind (IBKR integration)
- No authentication, CORS, or rate limiting overhead

## 🔄 Weekly Cron Job Example

```bash
#!/bin/bash
# Example weekly trading automation

# Start API server
cd /path/to/ibind_rest_api
uv run python run_server.py &
API_PID=$!

# Wait for server to start
sleep 5

# Check health
curl http://127.0.0.1:8080/health

# Execute trading logic
curl -X POST http://127.0.0.1:8080/percentage-order/SPY \
  -H "Content-Type: application/json" \
  -d '{
    "side": "BUY",
    "percentage_of_buying_power": 10,
    "percentage_below_market": 2,
    "time_in_force": "GTC"
  }'

# Stop server
kill $API_PID
```

---

**💡 Designed for automation - no web UI complexity!**
