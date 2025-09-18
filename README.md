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

### **Step 1: IBKR OAuth 1.0a Setup**

**✅ Good News**: With ibind library, OAuth setup is much simpler than generic IBKR setup!

**Prerequisites:**
- IBKR "Pro" account (individual accounts work too!)
- `openssl` installed on your machine

1. **Generate OAuth Keys:**
   ```bash
   # Generate all required keys
   openssl genrsa -out private_signature.pem 2048
   openssl rsa -in private_signature.pem -outform PEM -pubout -out public_signature.pem
   openssl genrsa -out private_encryption.pem 2048
   openssl rsa -in private_encryption.pem -outform PEM -pubout -out public_encryption.pem
   openssl dhparam -out dhparam.pem 2048
   ```

2. **IBKR OAuth Setup:**
   - Visit: [IBKR OAuth Setup Page](https://ndcdyn.interactivebrokers.com/sso/Login?action=OAUTH&RL=1&ip2loc=US)
   - **Consumer Key**: Choose your own 9-character password (A-Z only)
   - **Upload Public Keys**: `public_signature.pem`, `public_encryption.pem`, `dhparam.pem`
   - **Generate Tokens**: Copy Access Token & Access Token Secret (⚠️ won't reappear!)
   - **Enable OAuth Access**: Toggle the switch

3. **Extract DH Prime:**
   ```python
   # Save as extract_dh_prime.py and run
   import subprocess, re
   result = subprocess.run(["openssl", "dhparam", "-in", "dhparam.pem", "-text"], 
                          capture_output=True, text=True).stdout
   match = re.search(r"(?:prime|P):\s*((?:\s*[0-9a-fA-F:]+\s*)+)", result)
   print(re.sub(r"[\s:]", "", match.group(1)) if match else "No prime found.")
   ```

4. **Environment Variables:**
   ```bash
   export IBIND_USE_OAUTH=True
   export IBIND_OAUTH1A_CONSUMER_KEY="YOUR_9_CHAR_KEY"
   export IBIND_OAUTH1A_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
   export IBIND_OAUTH1A_ACCESS_TOKEN_SECRET="YOUR_ACCESS_TOKEN_SECRET"
   export IBIND_OAUTH1A_DH_PRIME="YOUR_DH_PRIME_HEX_STRING"
   export IBIND_OAUTH1A_ENCRYPTION_KEY_FP="./private_encryption.pem"
   export IBIND_OAUTH1A_SIGNATURE_KEY_FP="./private_signature.pem"
   ```

5. **Install OAuth Dependencies:**
   ```bash
   uv add ibind[oauth]
   ```

**📚 Official Guide:**
- [Voyz ibind OAuth 1.0a Wiki](https://github.com/Voyz/ibind/wiki/OAuth-1.0a) (Complete setup guide)
- [ibind OAuth Example](https://github.com/Voyz/ibind/blob/master/examples/rest_08_oauth.py)

### **Step 2: Google Sheets Setup**

1. **Google Cloud Console Setup:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project (or select existing one)
   - Navigate to **APIs & Services → Library**
   - Enable **Google Sheets API** and **Google Drive API**

2. **Create Service Account:**
   - Go to **IAM & Admin → Service Accounts**  
   - Click **+ CREATE SERVICE ACCOUNT**
   - Give it a name (e.g., "sheets-automation")
   - Grant role: **Editor** (for Google Sheets access)

3. **Download Credentials:**
   - Click on your service account → **Keys** tab
   - **ADD KEY** → **Create new key** → **JSON**
   - Download and save as `google_sheets_credentials.json` in project root

4. **Create & Share Google Sheet:**
   - Create sheet with columns: `Status | Stock Symbol | Amount (USD) | Frequency | Log`
   - Click **Share** → Add service account email (from JSON file)
   - Grant **Editor** permissions
   - Copy sheet URL

**📚 Resources:**
- [Google Sheets API Quickstart](https://developers.google.com/sheets/api/quickstart/python)
- [Service Account Authentication](https://cloud.google.com/iam/docs/service-accounts-create)

### **Step 3: Discord Notifications**

1. **Create Discord Webhook:**
   - Open your Discord server
   - Right-click on the channel where you want notifications
   - **Edit Channel** → **Integrations** → **Webhooks**
   - Click **New Webhook** 
   - Copy the webhook URL (starts with `https://discord.com/api/webhooks/...`)

**📚 Resources:**
- [Discord Webhook Setup Guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

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

**🎯 Service Management:**
```bash
# Check if service is running
uv run python service.py status

# Stop the service
uv run python service.py stop

# Restart the service  
uv run python service.py restart
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
# Start the service (daemon mode)
uv run python service.py start

# Check service status
uv run python service.py status

# Stop the service
uv run python service.py stop

# Restart the service
uv run python service.py restart

# View live logs
uv run python service.py logs -f

# Manual test execution
uv run python service.py execute
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