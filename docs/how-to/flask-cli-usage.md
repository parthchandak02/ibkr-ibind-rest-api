# 🛠️ Flask CLI Usage Guide

This guide shows you how to use the integrated Flask CLI commands for managing your trading operations.

## 🆕 **What Changed**

### ❌ **Old Way (Separate Scripts):**
```bash
# Old separate scripts approach
python scripts/rebalance_with_market.py --tickers AAPL TSLA
python scripts/view_open_orders.py  
python scripts/cancel_duplicates.py
```

### ✅ **New Way (Flask CLI):**
```bash
# Modern Flask CLI approach  
uv run flask trading rebalance --tickers AAPL TSLA --dry-run
uv run flask orders view
uv run flask orders cancel-duplicates --dry-run
uv run flask portfolio export --format csv
```

## 📋 **Available Commands**

### **1. Trading Commands**
```bash
# Rebalance portfolio (sell percentage of stocks)
uv run flask trading rebalance --tickers AAPL TSLA MSFT --percentage 25 --dry-run

# Options:
--tickers, -t        Stock tickers (required, multiple)
--percentage, -p     Percentage to sell (default: 25%)  
--order-type, -o     market or limit (default: market)
--dry-run, -d        Preview only, don't execute
```

### **2. Order Management**
```bash
# View live orders with rich formatting
uv run flask orders view --sort-by ticker

# Cancel duplicate orders  
uv run flask orders cancel-duplicates --dry-run

# Options:
--refresh, -r        Auto-refresh interval (default: 5s)
--sort-by, -s        Sort by: ticker, side, quantity, price
--dry-run, -d        Preview duplicates without cancelling
```

### **3. Portfolio Analysis**
```bash
# Export portfolio in different formats
uv run flask portfolio export --format table
uv run flask portfolio export --format json --output portfolio.json
uv run flask portfolio export --format csv --output portfolio.csv

# Options:
--format, -f         Output format: table, json, csv
--output, -o         Output file (default: stdout)
```

## 🎯 **Common Usage Examples**

### **Dry Run Portfolio Rebalancing**
```bash
# Preview what trades would be executed
uv run flask trading rebalance --tickers AAPL TSLA MSFT --percentage 30 --dry-run
```

### **Live Trading (Careful!)**
```bash
# Execute actual trades (remove --dry-run)
uv run flask trading rebalance --tickers AAPL --percentage 10
```

### **Monitor Orders**
```bash
# View current orders sorted by ticker
uv run flask orders view --sort-by ticker

# Auto-refresh every 3 seconds
uv run flask orders view --refresh 3
```

### **Export Portfolio Data**
```bash
# Quick table view
uv run flask portfolio export

# Export to CSV for analysis
uv run flask portfolio export --format csv --output ~/portfolio_$(date +%Y%m%d).csv

# Export JSON for programmatic use  
uv run flask portfolio export --format json --output portfolio.json
```

## 🔧 **Setup Requirements**

### **1. Install Dependencies**
```bash
uv sync  # Installs all requirements including rich and click
```

### **2. Set Flask App Environment**
```bash
export FLASK_APP=backend.api:app
# Or add to your ~/.zshrc or ~/.bashrc
```

### **3. Verify Installation**
```bash
# Check available commands
uv run flask --help

# Check trading commands
uv run flask trading --help
```

## 🎨 **Features**

### **Rich Terminal Output**
- ✅ Colored tables and progress bars
- ✅ Interactive confirmations
- ✅ Real-time progress indicators
- ✅ Professional formatting

### **Safety Features**
- ✅ `--dry-run` mode for all trading commands
- ✅ Interactive confirmations for live trades
- ✅ Input validation and error handling
- ✅ Rate limiting for API calls

### **Integration Benefits**
- ✅ Shares Flask app configuration
- ✅ Same IBKR client connection
- ✅ Consistent error handling
- ✅ No duplicate API authentication

## 🆚 **Migration Guide**

### **Script → CLI Command Mapping**

| Old Script | New CLI Command |
|------------|-----------------|
| `scripts/rebalance_with_market.py` | `uv run flask trading rebalance --order-type market` |
| `scripts/rebalance_with_limit.py` | `uv run flask trading rebalance --order-type limit` |
| `scripts/view_open_orders.py` | `uv run flask orders view` |
| `scripts/cancel_duplicates.py` | `uv run flask orders cancel-duplicates` |

### **Parameter Changes**

| Old Script Parameter | New CLI Parameter |
|---------------------|-------------------|
| `--tickers AAPL TSLA` | `--tickers AAPL TSLA` |
| `--dry_run` | `--dry-run` |
| No equivalent | `--percentage 25` |
| No equivalent | `--order-type market` |

## 🚨 **Important Notes**

### **Environment Setup**
Make sure your Flask environment is properly configured:
- ✅ IBKR OAuth files in place
- ✅ GitHub token configured (if using workflow triggers)
- ✅ All dependencies installed via UV

### **Safety First**
- 🔥 **Always use `--dry-run` first** to preview trades
- 🔥 **Double-check tickers** before executing
- 🔥 **Start with small percentages** for testing

### **Performance**
- ⚡ CLI commands share Flask app context (faster)
- ⚡ No HTTP overhead (direct function calls)
- ⚡ Reuses existing IBKR connection

## 🎪 **Advanced Usage**

### **Combining Commands**
```bash
# Check portfolio, then rebalance
uv run flask portfolio export --format table
uv run flask trading rebalance --tickers AAPL TSLA --percentage 15 --dry-run

# Clean up orders after trading
uv run flask orders view
uv run flask orders cancel-duplicates --dry-run
```

### **Scripting and Automation**
```bash
#!/bin/bash
# Daily portfolio management script

echo "📊 Current Portfolio:"
uv run flask portfolio export --format table

echo -e "\n🔄 Rebalancing Top Positions:"
uv run flask trading rebalance --tickers AAPL MSFT GOOGL --percentage 5 --dry-run

echo -e "\n📋 Current Orders:"
uv run flask orders view
```

## 🆘 **Troubleshooting**

### **Command Not Found**
```bash
# Make sure Flask app is set
export FLASK_APP=backend.api:app

# Verify with
uv run flask --help
```

### **IBKR Connection Issues**
```bash
# Test Flask server first
uv run python run_server.py --port 8080

# Then try CLI commands
uv run flask trading --help
```

### **Rich Formatting Issues**
```bash
# Install rich if missing
uv add rich

# Test with simple command
uv run flask portfolio export --format table
```

---

## 🎉 **Ready to Trade!**

You now have a powerful, integrated CLI system that's:
- ✅ Faster and more reliable than separate scripts
- ✅ Uses modern Flask CLI patterns (2025 standards)
- ✅ Provides rich terminal output
- ✅ Includes comprehensive safety features

Start with dry runs, then graduate to live trading when you're confident!

```bash
# Your first command:
uv run flask portfolio export
``` 