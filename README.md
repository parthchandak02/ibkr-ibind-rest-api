# 🚀 IBKR Enterprise Trading System

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![IBKR](https://img.shields.io/badge/IBKR-API-orange.svg)](https://www.interactivebrokers.com/)

**Professional automated recurring orders for Interactive Brokers.** Enterprise-grade Python system with quantity-based execution, sequential Google Sheets logging, and rich Discord notifications.

## ✨ Features

- 🔄 **Automated Trading** - Daily/Weekly/Monthly recurring orders
- 📊 **Google Sheets Integration** - Order management and execution logging  
- 📧 **Discord Notifications** - Professional rich embed alerts
- 🏦 **IBKR API** - Direct integration with Interactive Brokers
- 🎯 **Quantity-Based Orders** - Precise share control (no fractional issues)
- 📈 **Sequential Logging** - Complete execution history tracking
- ⚙️ **Enterprise Architecture** - Type-safe, validated, configurable

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/parthchandak02/ibkr-ibind-rest-api.git
cd ibkr-ibind-rest-api
uv sync

# Configure (see setup below)
cp config.example.json config.json
# Edit config.json with your credentials

# Start system
uv run python service.py start

# Verify running
curl http://127.0.0.1:8082/health
```

**Your orders execute automatically at 9 AM EST daily/weekly/monthly.**

## 📋 Setup

### 1. IBKR OAuth Setup

Generate keys and configure IBKR OAuth 1.0a:

```bash
# Generate required keys
openssl genrsa -out private_signature.pem 2048
openssl genrsa -out private_encryption.pem 2048
openssl dhparam -out dhparam.pem 2048

# Move to oauth directory
mkdir -p live_trading_oauth_files
mv private_*.pem live_trading_oauth_files/
```

**IBKR Portal Setup:**
1. Visit [IBKR OAuth Setup](https://ndcdyn.interactivebrokers.com/sso/Login?action=OAUTH&RL=1)
2. Upload public keys (`public_signature.pem`, `public_encryption.pem`, `dhparam.pem`)
3. Copy Consumer Key, Access Token, Access Token Secret
4. Extract DH Prime with: `openssl dhparam -in dhparam.pem -text | grep -A 50 "prime:" | tr -d '\n :' | sed 's/prime//'`

### 2. Google Sheets Setup

1. **Google Cloud Console:**
   - Create project → Enable Sheets API & Drive API
   - Create Service Account → Download JSON credentials

2. **Sheet Setup:**
   - Create sheet with columns: `Status | Stock Symbol | Price | Amount | Qty to buy | Frequency | Log`
   - Share with service account email (Editor permissions)

### 3. Discord Webhook

1. Discord Server → Channel Settings → Webhooks → New Webhook
2. Copy webhook URL

### 4. Configuration

Edit `config.json` with your credentials:

```json
{
  "live_trading": { "oauth": { /* IBKR credentials */ } },
  "google_sheets": { "credentials": { /* Service account JSON */ } },
  "discord": { "webhook_url": "https://discord.com/api/webhooks/..." }
}
```

## 📊 Usage

### Google Sheet Format
| Status | Stock Symbol | Price | Amount | Qty to buy | Frequency | Log |
|--------|-------------|-------|--------|-----------|-----------|-----|
| Active | AAPL | 175.50 | 175.50 | 1 | Weekly | *(auto-filled)* |
| Active | WDH | 1.90 | 1.90 | 1 | Daily | *(auto-filled)* |

### Frequency Options
- **Daily** → Every day at 9 AM EST
- **Weekly** → Mondays at 9 AM EST  
- **Monthly** → 1st of month at 9 AM EST

### Service Management
```bash
uv run python service.py start    # Start automated system
uv run python service.py status   # Check if running
uv run python service.py stop     # Stop system
uv run python service.py logs     # View execution logs
```

### Manual Execution
```bash
# Test single execution
curl -X POST http://127.0.0.1:8082/recurring/execute

# View orders
curl http://127.0.0.1:8082/orders
```

## 🔧 API Endpoints

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/health` | GET | System health |
| `/orders` | GET | List orders |
| `/order/symbol` | POST | Place order |
| `/recurring/execute` | POST | Trigger orders |
| `/recurring/status` | GET | System status |

## 📱 What You Get

**Automated Execution:**
- Daily orders → Execute every day at 9 AM EST
- Weekly orders → Execute Mondays at 9 AM EST  
- Monthly orders → Execute 1st of month at 9 AM EST

**Discord Notifications:**
- 🟢 Professional rich embeds with order details
- 📊 Execution summary with success/failure counts
- 🏦 Order IDs and market prices included

**Google Sheets Logging:**
- Sequential execution history in columns G→H→I→J
- Format: `✅ 2025-09-18 09:00:15: 1 shares @ $175.50 | ID: 1234567`

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "IBKR client not available" | Check OAuth files in `live_trading_oauth_files/` |
| "Google Sheets auth failed" | Verify service account has Editor access to sheet |
| "Service not running" | Run `uv run python service.py status` |
| "Config errors" | Validate JSON: `python -m json.tool config.json` |

**Health Checks:**
```bash
curl http://127.0.0.1:8082/health        # API health
curl http://127.0.0.1:8081/service/status # Service status
```

## 🛠️ Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## 📁 Project Structure

```
├── backend/          # Core trading logic & API
├── service/          # Background automation service
├── scripts/          # Utility tools (monitoring, cleanup)
├── config.json       # All credentials & settings
└── service.py        # Service management
```

## 🔒 Security

- **Local only** - Runs on 127.0.0.1 (no external access)
- **No API authentication** - Designed for trusted local environment
- **Credentials in config.json** - Keep this file secure and local

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/parthchandak02/ibkr-ibind-rest-api/issues)
- 💬 [Discussions](https://github.com/parthchandak02/ibkr-ibind-rest-api/discussions)

---

**🎯 Enterprise-grade automated trading made simple.**