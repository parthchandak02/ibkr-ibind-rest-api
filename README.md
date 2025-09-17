# 🚀 IBKR Trading API

**Automated recurring orders for Interactive Brokers.** Reads orders from Google Sheets, executes via IBKR API, sends Discord notifications.

---

## ⚡ **Quick Start**

```bash
# 1. Clone and install
git clone <your-repo>
cd ibind_rest_api
uv sync

# 2. Configure credentials (see setup below)
# 3. Start service
uv run python service.py start
```

**Your orders will now execute automatically every day at 9 AM EST.**

---

## 🔧 **Complete Setup Guide**

### **Step 1: IBKR Credentials**

1. **Get IBKR OAuth Access:**
   - Log into IBKR Client Portal
   - Go to Settings → API → Create API Key
   - Enable "Live Trading" permissions
   - Note down: `Consumer Key`, `Access Token`, `Access Token Secret`

2. **Generate OAuth Keys:**
   ```bash
   # Use IBKR's OAuth tool to generate RSA keys
   # This creates: private_encryption.pem + private_signature.pem
   ```

3. **Create `config.json`:**
   ```json
   {
     "live_trading": {
       "oauth": {
         "consumer_key": "YOUR_CONSUMER_KEY",
         "access_token": "YOUR_ACCESS_TOKEN", 
         "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET",
         "dh_prime": "YOUR_DH_PRIME",
         "realm": "limited_poa"
       }
     }
   }
   ```

4. **Place OAuth Files:**
   ```
   live_trading_oauth_files/
   ├── private_encryption.pem
   └── private_signature.pem
   ```

### **Step 2: Google Sheets Setup**

1. **Create Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create project → Enable Sheets API
   - Create Service Account → Download JSON key

2. **Save Credentials:**
   ```bash
   # Save as: google_sheets_credentials.json
   ```

3. **Create Google Sheet:**
   - Create sheet with columns: `Status | Stock Symbol | Amount (USD) | Frequency | Log`
   - Share sheet with service account email (from JSON)
   - Copy sheet URL

### **Step 3: Discord Notifications**

1. **Create Discord Webhook:**
   - Discord Server → Channel Settings → Integrations → Webhooks
   - Copy webhook URL

### **Step 4: Environment Variables**

```bash
export GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK"
export GOOGLE_SHEETS_CREDENTIALS_PATH="./google_sheets_credentials.json"
export IBIND_TRADING_ENV="live_trading"  # or "paper_trading"
```

### **Step 5: Test & Run**

```bash
# Test API server
uv run python run_server.py
curl http://127.0.0.1:8080/health

# Test recurring orders manually  
uv run python service.py execute

# Start persistent service
uv run python service.py start
```

---

## 📊 **Usage**

### **Google Sheet Format:**
| Status | Stock Symbol | Amount (USD) | Frequency | Log |
|--------|-------------|-------------|-----------|-----|
| Active | AAPL | 100 | Weekly | *(auto-filled)* |
| Active | SPY | 50 | Daily | *(auto-filled)* |

### **Frequency Rules:**
- **Daily** → Every day at 9 AM EST
- **Weekly** → Mondays at 9 AM EST  
- **Monthly** → 1st of month at 9 AM EST

### **Service Management:**
```bash
# Check status
uv run python service.py status

# View logs
uv run python service.py logs -f

# Stop/restart
uv run python service.py stop/restart
```

---

## 🎯 **API Endpoints**

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System health check |
| `GET /account` | Account info + positions |
| `POST /order/symbol` | Place order by symbol |
| `POST /recurring/execute` | Manual trigger |
| `GET /recurring/status` | Automation status |

### **Example Usage:**
```bash
# Place order
curl -X POST http://127.0.0.1:8080/order/symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"BUY","quantity":1,"order_type":"MKT"}'

# Trigger recurring orders
curl -X POST http://127.0.0.1:8080/recurring/execute
```

---

## 📱 **What You Get**

### **Automated Execution:**
- ✅ **Daily orders** execute every day at 9 AM EST
- ✅ **Weekly orders** execute Mondays at 9 AM EST
- ✅ **Monthly orders** execute 1st of month at 9 AM EST

### **Discord Notifications:**
```
🚀 Recurring Orders Executed Successfully

📊 Summary: Total: 2, Success: 2, Failed: 0
💰 Total Investment: $621.25

📋 Order Details:
🟢 AAPL: 1 shares @ $175.50 ($175.50)
   📋 Order ID: REC123456789
🟢 SPY: 1 shares @ $445.75 ($445.75)
   📋 Order ID: REC123456790
```

### **Google Sheets Logging:**
```
✅ 2025-09-17 09:00:15 EST: AAPL - 1 shares @ $175.50 ($175.50) | Order ID: REC123456789 | Frequency: Weekly
```

---

## 🔒 **Security**

- **Local only** - API runs on 127.0.0.1 (no external access)
- **No authentication** - designed for trusted local environment  
- **Service account** - Google Sheets access via service account
- **OAuth1a** - IBKR authentication via industry standard

---

## 🎯 **Perfect For**

✅ **Dollar-cost averaging** - regular recurring purchases  
✅ **Portfolio rebalancing** - systematic adjustments  
✅ **Automated investing** - set-and-forget strategies  
✅ **Personal trading** - local automation without cloud dependencies  

---

## 📚 **Project Structure**

```
ibind_rest_api/
├── backend/           # Core trading logic & API
├── service/           # Background automation daemon  
├── docs/             # Documentation
├── examples/         # Usage examples
├── run_server.py     # API server
├── service.py        # Service manager
└── config.json       # IBKR credentials
```

---

## 🧪 **Testing**

```bash
# Run test suite
uv run pytest tests/

# Test specific components  
uv run python tests/test_recurring_system.py
```

---

## 📞 **Troubleshooting**

### **Common Issues:**

1. **"IBKR client not available"**
   - Check `config.json` credentials
   - Verify OAuth files in `live_trading_oauth_files/`

2. **"Google Sheets authentication failed"**
   - Check `google_sheets_credentials.json` exists
   - Verify service account has sheet access

3. **"Service not running"**
   - Check: `uv run python service.py status`
   - View logs: `uv run python service.py logs`

### **Health Checks:**
```bash
# API health
curl http://127.0.0.1:8080/health

# Service status  
curl http://127.0.0.1:8081/service/status
```

---

**🚀 Enterprise-grade automated trading made simple.**