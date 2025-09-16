# 🚀 IBKR Trading API

Lightweight REST API for Interactive Brokers trading with auto-generated documentation.

## ⚡ Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Start backend API
uv run python run_server.py

# 3. Start frontend (optional)
cd frontend && npm run dev
```

**API Server**: http://localhost:8080  
**Frontend**: http://localhost:4321

## 📚 API Documentation

**Auto-generated, always up-to-date documentation:**
- **[Swagger UI](http://localhost:8080/docs)** - Interactive API testing
- **[ReDoc](http://localhost:8080/redoc)** - Beautiful documentation
- **[OpenAPI JSON](http://localhost:8080/openapi.json)** - API specification

## 🔑 Authentication

Generate API key:
```bash
uv run python utils/generate_key.py --name "MyApp"
```

Use in requests:
```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:8080/health
```

## 🎯 Core Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System status |
| `GET /account` | Account info + positions |
| `GET /positions?limit=200` | Portfolio positions |
| `GET /resolve/{symbol}` | Symbol → Contract ID |
| `POST /order` | Place market/limit orders |
| `POST /percentage-limit-order/{symbol}` | Smart percentage-based orders |

## 📱 Features

- **Real-time trading** with 147+ positions
- **Percentage-based orders** (consistent BUY/SELL API)
- **Extended hours trading** support
- **Modern web interface** with interactive tables
- **Auto-updating docs** - never out of sync

## 🛠️ Configuration

1. **OAuth Setup**: Add IBKR OAuth files to `live_trading_oauth_files/`
2. **Environment**: Set `IBIND_TRADING_ENV=live_trading`
3. **Port**: Set `PORT=8080` (optional)

## 📦 Dependencies

- Python 3.13+
- Flask (REST API)
- ibind (IBKR integration)
- rich (CLI output)

---

**💡 Documentation is auto-generated from code - always accurate!**