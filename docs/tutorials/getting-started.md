# 🚀 Getting Started Tutorial

Learn how to set up and run your IBKR trading server from scratch.

## Prerequisites

- **Python 3.13+** with UV installed
- **Interactive Brokers account** (paper trading recommended for testing)
- **GitHub account** with repository access
- **Basic understanding** of REST APIs and trading concepts

---

## Step 1: Environment Setup

### Install UV (if not already installed)
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.sh | iex"
```

### Clone the Repository
```bash
git clone https://github.com/parthchandak02/ibkr-ibind-rest-api.git
cd ibkr-ibind-rest-api
```

### Install Dependencies
```bash
# Install all dependencies using UV
uv sync

# This replaces the old pip install -r requirements.txt approach
# UV reads from pyproject.toml and creates a uv.lock file
```

---

## Step 2: Configure IBKR Connection

### Set Up Your Trading Account
1. **Open Interactive Brokers account** (if you don't have one)
2. **Enable API access** in your account settings
3. **Download IB Gateway** or TWS (Trader Workstation)
4. **Configure paper trading** for safe testing

### Test IBKR Connection
```bash
# Start the server (it will auto-connect to IBKR)
uv run python run_server.py --port 8080
```

**Expected output:**
```
✅ IBKR Client initialized successfully
✅ Connected to account: U14716312 (Paper)
✅ Server running on http://localhost:8080
```

---

## Step 3: Test Basic Functionality

### Generate an API Key
```bash
# Generate a test API key for authentication
uv run python generate_test_api_key.py
```

**Output:**
```
✅ Generated API key for testing: YOUR_API_KEY_PLACEHOLDER
📝 Use this in your test scripts with header: X-API-Key: [key]
```

### Test the Health Endpoint
```bash
# Test server health (requires API key)
curl -H "X-API-Key: YOUR_API_KEY_HERE" http://localhost:8080/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T03:19:43.250404",
  "ibkr_connected": true,
  "account_id": "U14716312"
}
```

---

## Step 4: Set Up GitHub Actions

### Configure GitHub Token
1. **Go to GitHub Settings** → Developer settings → Personal access tokens
2. **Generate new token** with `repo` and `actions` permissions
3. **Add to repository secrets** as `GITHUB_TOKEN`

### Test Workflow Trigger
```bash
# Update the test script with your API key
# Edit test_workflow_trigger.py and replace REPLACE_WITH_YOUR_API_KEY

# Run the workflow trigger test
uv run python test_workflow_trigger.py
```

**Expected output:**
```json
{
  "message": "Workflow triggered successfully",
  "status": "success",
  "triggered_at": "2025-01-28T03:19:43.250404",
  "workflow_params": {
    "action": "BUY",
    "limit_price": 150.0,
    "quantity": 1,
    "symbol": "AAPL"
  }
}
```

---

## Step 5: Verify End-to-End Flow

### Check GitHub Actions
1. **Go to your repository** on GitHub
2. **Click the "Actions" tab**
3. **Look for the triggered workflow** - you should see "Trading Trigger - AAPL Test Order"
4. **Verify the workflow ran successfully**

### Test Portfolio Management
```bash
# View your current portfolio
uv run flask --app backend.api:app portfolio view

# Check open orders
uv run flask --app backend.api:app orders view

# Test a small market order (paper trading!)
uv run flask --app backend.api:app trading execute --symbol AAPL --action BUY --quantity 1 --dry-run
```

---

## 🎉 Congratulations!

You now have a fully functional IBKR trading server with GitHub Actions integration!

## What You've Accomplished

✅ **Server Setup**: Flask server running with IBKR connection  
✅ **API Authentication**: Working API key system  
✅ **GitHub Integration**: Workflow triggers via REST API  
✅ **Trading Commands**: Flask CLI for portfolio management  
✅ **End-to-End Testing**: Complete workflow verification  

## Next Steps

- **Learn more commands**: Check out [Flask CLI Usage](../how-to/flask-cli-usage.md)
- **Understand the architecture**: Read [System Architecture](../explanations/architecture.md)  
- **Execute your first real trade**: Follow [First Trade Execution](first-trade.md)
- **Explore the API**: See [API Endpoints Reference](../reference/api-endpoints.md)

## 🆘 Troubleshooting

**Server won't start?**
- Check if IBKR Gateway/TWS is running
- Verify API permissions in your IB account
- Check port 8080 isn't already in use

**Workflow trigger failing?**
- Verify GitHub token has correct permissions
- Check API key is valid and not expired
- Ensure repository_dispatch event is configured

**Import errors?**
- Run `uv sync` to ensure all dependencies are installed
- Make sure you're using UV, not pip
- Check you're in the correct directory

Need more help? Check our [How-to Guides](../how-to/) or [open an issue](https://github.com/parthchandak02/ibkr-ibind-rest-api/issues)! 