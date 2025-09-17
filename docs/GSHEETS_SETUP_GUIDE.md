# 📊 Google Sheets Integration Setup Guide

## 🎯 **Quick Setup (15 minutes)**

### **Step 1: Google Cloud Console Setup**

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create/Select Project**: 
   - Click "Select a project" → "New Project"
   - Name it something like "IBKR-Trading-Sheets"
3. **Enable APIs**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API" → Enable
   - Search for "Google Drive API" → Enable (for file access)

### **Step 2: Create Service Account**

1. **Go to Credentials**:
   - "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
2. **Configure Service Account**:
   - Name: `ibkr-trading-bot`
   - ID: `ibkr-trading-bot` (auto-generated)
   - Description: "Service account for IBKR trading automation"
   - Click "Create and Continue"
3. **Skip role assignment** (click "Continue" then "Done")

### **Step 3: Generate Key File**

1. **Find your service account** in the credentials list
2. **Click on the email** to open details
3. **Go to "Keys" tab** → "Add Key" → "Create New Key"
4. **Select "JSON"** → Create
5. **Download the file** and save as `google_sheets_credentials.json`

### **Step 4: Share Your Spreadsheet**

1. **Open your Google Sheet**: https://docs.google.com/spreadsheets/d/1CwyNMN_YRhU5IaYaG1OXaBGzgoYkBtF5rc9sO9Nyw48/edit
2. **Click "Share"** button
3. **Add the service account email** (from the JSON file: `client_email` field)
4. **Give "Editor" permissions**
5. **Click "Send"**

### **Step 5: Install Dependencies**

```bash
uv sync  # This will install gspread and google-auth
```

### **Step 6: Test the Connection**

```python
from backend.sheets_integration import get_sheets_client

# Test reading your sheet
sheets = get_sheets_client("google_sheets_credentials.json")
url = "https://docs.google.com/spreadsheets/d/1CwyNMN_YRhU5IaYaG1OXaBGzgoYkBtF5rc9sO9Nyw48/edit"

try:
    spreadsheet = sheets.open_spreadsheet_by_url(url)
    worksheet = sheets.get_worksheet(spreadsheet, index=0)
    data = sheets.read_all_records(worksheet)
    print(f"✅ Success! Found {len(data)} records")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🔧 **Integration with IBKR API**

### **Option 1: Manual API Endpoints**

Add these endpoints to your `backend/api.py`:

```python
from .sheets_integration import get_sheets_client

@app.route("/sheets/log-trade", methods=["POST"])
def log_trade_to_sheets():
    """Log a trade to Google Sheets."""
    data = request.json
    sheets = get_sheets_client()
    
    try:
        sheets.log_trade(
            spreadsheet_url=data["spreadsheet_url"],
            symbol=data["symbol"],
            side=data["side"],
            quantity=data["quantity"],
            price=data["price"],
            order_type=data.get("order_type", "MKT")
        )
        return jsonify({"status": "success", "message": "Trade logged to sheets"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/sheets/update-portfolio", methods=["POST"])
def update_portfolio_in_sheets():
    """Update portfolio snapshot in Google Sheets."""
    data = request.json
    sheets = get_sheets_client()
    
    try:
        # Get current positions
        from .account_operations import fetch_all_positions_paginated
        positions = fetch_all_positions_paginated()
        
        sheets.update_portfolio_snapshot(
            spreadsheet_url=data["spreadsheet_url"],
            positions_data=positions
        )
        return jsonify({"status": "success", "message": "Portfolio updated in sheets"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

### **Option 2: Automatic Integration**

Modify your existing order placement to automatically log to sheets:

```python
# In your order placement function, add:
def place_order_with_sheets_logging(order_data, spreadsheet_url=None):
    # Place the order normally
    result = place_order_normal(order_data)
    
    # If successful and sheets URL provided, log it
    if result["status"] == "success" and spreadsheet_url:
        try:
            sheets = get_sheets_client()
            sheets.log_trade(
                spreadsheet_url=spreadsheet_url,
                symbol=order_data["symbol"],
                side=order_data["side"],
                quantity=order_data["quantity"],
                price=order_data.get("price", 0)
            )
        except Exception as e:
            logger.warning(f"Failed to log to sheets: {e}")
    
    return result
```

---

## 🎯 **Common Use Cases**

### **1. Trade Logging**
```python
sheets.log_trade(
    spreadsheet_url="your_sheet_url",
    symbol="AAPL",
    side="BUY", 
    quantity=100,
    price=150.50
)
```

### **2. Portfolio Tracking**
```python
positions = get_current_positions()
sheets.update_portfolio_snapshot(
    spreadsheet_url="your_sheet_url",
    positions_data=positions
)
```

### **3. Reading Trading Signals**
```python
# Read buy/sell signals from a sheet
signals = sheets.read_all_records(worksheet)
for signal in signals:
    if signal['Action'] == 'BUY' and signal['Status'] == 'Pending':
        place_order(signal['Symbol'], signal['Quantity'])
```

---

## 🔒 **Security Best Practices**

1. **Store credentials securely**:
   ```bash
   # Add to .gitignore
   echo "google_sheets_credentials.json" >> .gitignore
   ```

2. **Use environment variables**:
   ```python
   import os
   CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "google_sheets_credentials.json")
   ```

3. **Minimal permissions**:
   - Only share sheets with the service account that need access
   - Use "Editor" only if you need write access

---

## ⚡ **Performance Tips**

1. **Batch operations** when possible:
   ```python
   # Instead of multiple append_row calls
   sheets.batch_update(worksheet, multiple_updates)
   ```

2. **Cache the client**:
   ```python
   # Create once, reuse many times
   sheets_client = get_sheets_client()
   ```

3. **Rate limiting**: Google Sheets API allows 500 requests per 100 seconds

---

## 🐛 **Common Issues & Solutions**

### **"Insufficient Permission" Error**
- ✅ Make sure you shared the sheet with the service account email
- ✅ Give "Editor" permissions

### **"File not found" Error**  
- ✅ Check the spreadsheet URL is correct
- ✅ Make sure the sheet is shared publicly or with the service account

### **"Authentication Error"**
- ✅ Verify the JSON credentials file path
- ✅ Check that both Google Sheets API and Drive API are enabled

---

## 🎉 **You're All Set!**

Your IBKR trading API can now seamlessly integrate with Google Sheets for:
- ✅ **Trade logging**
- ✅ **Portfolio tracking**  
- ✅ **Signal reading**
- ✅ **Data analysis**
- ✅ **Sharing with others**

**Total setup time: ~15 minutes**  
**Complexity: Low**  
**Maintenance: Minimal**
