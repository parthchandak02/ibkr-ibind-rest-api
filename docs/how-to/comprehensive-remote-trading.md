# 🚀 Comprehensive Remote Trading Guide

**Execute ANY backend operation remotely via GitHub Actions using 2025 best practices**

This guide shows you how to use the unified trading system that allows you to trigger all backend functions remotely via GitHub Actions, GitHub CLI, or REST API.

---

## 🎯 What You Can Do Remotely

### **Complete Functionality Access**
- ✅ **Trading Operations**: Buy, sell, rebalance portfolios
- ✅ **Portfolio Management**: View positions, performance, export data  
- ✅ **Order Management**: View, cancel, or manage all orders
- ✅ **Market Data**: Get quotes, prices, historical data
- ✅ **Account Operations**: View account info and positions
- ✅ **Data Export**: Generate CSV, JSON, Excel reports

### **Multiple Access Methods**
- 🖥️ **GitHub UI**: Point-and-click interface
- ⌨️ **GitHub CLI**: Command-line automation
- 🔌 **REST API**: Direct API integration
- 🤖 **External Triggers**: Repository dispatch events

---

## 🚀 Quick Start Examples

### **Method 1: GitHub UI (Easiest)**

1. **Go to your repository** → Actions tab
2. **Select "Comprehensive Trading Operations"** workflow
3. **Click "Run workflow"**
4. **Fill in the form**:
   - Operation Type: `trading`
   - Trading Action: `buy`
   - Symbol: `AAPL`
   - Quantity: `1`
   - Dry Run: `true` (for safety)
   - Environment: `paper`
5. **Click "Run workflow"**

### **Method 2: GitHub CLI (Automation)**

```bash
# Buy 1 share of AAPL (dry run)
gh workflow run comprehensive-trading.yml \
  -f operation_type=trading \
  -f trading_action=buy \
  -f symbol=AAPL \
  -f quantity=1 \
  -f dry_run=true \
  -f environment=paper

# View portfolio
gh workflow run comprehensive-trading.yml \
  -f operation_type=portfolio \
  -f portfolio_action=view \
  -f environment=paper

# Get market quotes for multiple symbols
gh workflow run comprehensive-trading.yml \
  -f operation_type=market_data \
  -f market_action=multiple_quotes \
  -f symbols_list="AAPL,TSLA,MSFT" \
  -f environment=paper
```

### **Method 3: REST API (Direct Integration)**

```bash
# Direct API call to your trading server
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "operation_type": "trading",
    "action": "buy",
    "symbol": "AAPL",
    "quantity": "1",
    "dry_run": true,
    "environment": "paper"
  }' \
  "https://your-trading-server.com/api/comprehensive-execute"
```

---

## 📋 Complete Operation Reference

### **Trading Operations**

| Action | Description | Required Fields | Optional Fields |
|--------|-------------|----------------|----------------|
| `rebalance` | Sell percentage of position | `symbol`, `quantity` (%) | `dry_run` |
| `buy` | Buy shares | `symbol`, `quantity` | `price` (for limit), `dry_run` |
| `sell` | Sell shares | `symbol`, `quantity` | `price` (for limit), `dry_run` |
| `market_order` | Execute at market price | `symbol`, `quantity` | `dry_run` |
| `limit_order` | Execute at specific price | `symbol`, `quantity`, `price` | `dry_run` |

**Example:**
```yaml
operation_type: trading
trading_action: rebalance
symbol: AAPL
quantity: "25"  # Sell 25% of AAPL position
dry_run: true
environment: paper
```

### **Portfolio Operations**

| Action | Description | Output |
|--------|-------------|--------|
| `view` | Complete portfolio overview | Account data + positions |
| `summary` | Portfolio summary | Key metrics |
| `positions` | Just position data | Position list |
| `performance` | Performance metrics | P&L and totals |

**Example:**
```yaml
operation_type: portfolio
portfolio_action: positions
export_format: json
environment: paper
```

### **Order Operations**

| Action | Description | Required Fields |
|--------|-------------|----------------|
| `view` | View all live orders | None |
| `cancel` | Cancel specific order | `order_id` |
| `cancel_all` | Cancel all orders | None |
| `cancel_duplicates` | Cancel duplicate orders | None |
| `history` | Order history | None |

**Example:**
```yaml
operation_type: orders
order_action: view
environment: paper
```

### **Market Data Operations**

| Action | Description | Required Fields |
|--------|-------------|----------------|
| `quote` | Single symbol quote | `symbol` |
| `price` | Current price | `symbol` |
| `multiple_quotes` | Multiple symbols | `symbols_list` |
| `history` | Historical data | `symbol` |

**Example:**
```yaml
operation_type: market_data
market_action: multiple_quotes
symbols_list: "AAPL,TSLA,MSFT,GOOGL"
environment: paper
```

### **Data Export Operations**

| Format | Description | Use Case |
|--------|-------------|----------|
| `csv` | Comma-separated values | Excel import |
| `json` | JSON format | API integration |
| `xlsx` | Excel format | Reports |

**Example:**
```yaml
operation_type: data_export
export_format: csv
environment: paper
```

---

## 🛡️ Safety Features

### **Dry Run Mode**
- **Always enabled by default** for safety
- **Simulates operations** without executing
- **Shows expected results** before real execution
- **Must explicitly disable** for live trading

### **Environment Separation**
- **Paper Trading**: Safe testing environment
- **Live Trading**: Real money (requires explicit selection)

### **API Authentication**
- **API Key Required**: All operations require valid authentication
- **Rate Limiting**: Prevents abuse and protects IBKR limits
- **Audit Logging**: Complete trail of all operations

---

## 🔧 Advanced Usage

### **Matrix Testing (Multiple Configurations)**

Create workflows that test multiple scenarios:

```yaml
strategy:
  matrix:
    symbol: [AAPL, TSLA, MSFT]
    action: [buy, sell]
    quantity: [1, 5, 10]
```

### **Conditional Execution**

Execute different operations based on conditions:

```yaml
- name: Execute Trade
  if: github.event.inputs.symbol != ''
  run: |
    # Only execute if symbol is provided
```

### **Environment-Specific Configuration**

Different settings for paper vs live trading:

```yaml
env:
  TRADING_SERVER_URL: ${{ 
    github.event.inputs.environment == 'live' 
    && secrets.LIVE_TRADING_URL 
    || secrets.PAPER_TRADING_URL 
  }}
```

---

## 📊 Response Format

All operations return standardized responses:

### **Success Response**
```json
{
  "status": "success",
  "operation_type": "trading",
  "timestamp": "2025-01-28T15:30:45.123Z",
  "dry_run": true,
  "environment": "paper",
  "data": {
    "action": "buy",
    "symbol": "AAPL",
    "quantity": 1,
    "order_type": "MKT",
    "result": "Order placed successfully"
  }
}
```

### **Error Response**
```json
{
  "status": "error",
  "operation_type": "trading",
  "timestamp": "2025-01-28T15:30:45.123Z",
  "error": "Symbol not found",
  "error_type": "SymbolResolutionError"
}
```

---

## 🚨 Security Best Practices

### **Repository Secrets Setup**
```bash
# Required secrets in your GitHub repository
TRADING_API_KEY          # Your API key
TRADING_SERVER_URL       # Your trading server URL
GITHUB_TOKEN            # For workflow triggers
```

### **API Key Management**
```bash
# Generate a new API key
uv run python generate_test_api_key.py

# Test API key validity
curl -H "X-API-Key: YOUR_KEY" https://your-server.com/health
```

### **Environment Isolation**
- **Always test in paper trading first**
- **Use different API keys for different environments**
- **Monitor all trading activities**
- **Set appropriate position limits**

---

## 🔍 Troubleshooting

### **Common Issues**

| Problem | Solution |
|---------|----------|
| "API key invalid" | Generate new key with `generate_test_api_key.py` |
| "IBKR client not available" | Check if trading server is running |
| "Symbol not found" | Verify symbol exists and is tradeable |
| "Insufficient positions" | Check portfolio has enough shares |

### **Debug Information**

Enable debug logging in workflows:
```yaml
- name: Debug Operation
  run: |
    echo "Operation: ${{ github.event.inputs.operation_type }}"
    echo "Symbol: ${{ github.event.inputs.symbol }}"
    echo "Dry Run: ${{ github.event.inputs.dry_run }}"
```

### **Testing Workflow**

1. **Start with dry run enabled**
2. **Test with small quantities**
3. **Verify in paper trading environment**
4. **Check workflow logs for errors**
5. **Only then proceed to live trading**

---

## 📈 Real-World Examples

### **Portfolio Rebalancing**
```bash
# Sell 25% of AAPL position
gh workflow run comprehensive-trading.yml \
  -f operation_type=trading \
  -f trading_action=rebalance \
  -f symbol=AAPL \
  -f quantity=25 \
  -f dry_run=false \
  -f environment=live
```

### **Market Data Collection**
```bash
# Collect prices for watchlist
gh workflow run comprehensive-trading.yml \
  -f operation_type=market_data \
  -f market_action=multiple_quotes \
  -f symbols_list="AAPL,TSLA,MSFT,GOOGL,AMZN"
```

### **Daily Portfolio Export**
```bash
# Export portfolio to CSV
gh workflow run comprehensive-trading.yml \
  -f operation_type=data_export \
  -f export_format=csv \
  -f environment=live
```

---

## 🎯 Next Steps

1. **Test the system** with dry run enabled
2. **Explore different operation types** to understand capabilities
3. **Set up automated workflows** for regular tasks
4. **Monitor and optimize** your trading strategies
5. **Scale up** to more complex operations

Ready to start? Check out the [Getting Started Tutorial](../tutorials/getting-started.md) or explore the [API Reference](../reference/api-endpoints.md)!

---

**⚠️ Remember: This system handles real money. Always test thoroughly in paper trading before using live accounts!** 