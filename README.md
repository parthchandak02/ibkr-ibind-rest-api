# 🚀 IBKR REST API

A secure RESTful API wrapper for Interactive Brokers (IBKR) trading platform.

## ⚡ Quick Start

### Local Development
```bash
# Activate virtual environment
source ~/aienv/bin/activate

# Generate API key
python3 utils/generate_key.py --name "My API Key"

# Start the server
python3 run_server.py --env live_trading --port 8080 --debug
```

### Test Locally
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" http://localhost:8080/health
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API health check |
| `/account` | GET | Account information |
| `/positions` | GET | Portfolio positions |
| `/orders` | GET | Order history |
| `/order` | POST | Place new order |

## 🔐 Authentication

All requests require an API key in the header:
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" https://your-api.com/health
```

## 📁 Project Structure

```
ibind_rest_api/
├── run_server.py          # Entry point
├── src/                   # Main application
│   ├── application.py     # Application class
│   ├── api.py            # Flask REST API
│   ├── auth.py           # Authentication
│   ├── config.py         # Configuration
│   └── utils.py          # IBKR client utilities
└── utils/                 # Utility scripts
    └── generate_key.py    # API key generator
```

## ☁️ Deploy to Render.com (RECOMMENDED)

### Why Render?
- ✅ 750 free hours/month (continuous running)
- ✅ Automatic HTTPS
- ✅ Easy environment variables
- ✅ Git-based deployment

### Step-by-Step Deployment:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Sign up at Render.com**:
   - Go to https://render.com
   - Sign up with your GitHub account

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your `ibind_rest_api` repo

4. **Configure Service**:
   - **Name**: `ibkr-api`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: `Free`

5. **Environment Variables**:
   ```
   IBIND_TRADING_ENV=live_trading
   PORT=8080
   ```

6. **Upload Files** (via Render dashboard):
   - Upload your `config.json`
   - Upload your `api_keys.json`
   - Upload your `live_trading_oauth_files/` directory

7. **Deploy**: Click "Create Web Service"

### Test Your Deployment:
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" https://your-app.onrender.com/health
```

## 📱 Google Apps Script Integration

### Basic Functions:
```javascript
function getAccountInfo() {
  const apiKey = "YOUR_API_KEY_HERE";
  const baseUrl = "https://your-app.onrender.com";
  
  const response = UrlFetchApp.fetch(`${baseUrl}/account`, {
    'headers': {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    }
  });
  
  return JSON.parse(response.getContentText());
}

function getPositions() {
  const apiKey = "YOUR_API_KEY_HERE";
  const baseUrl = "https://your-app.onrender.com";
  
  const response = UrlFetchApp.fetch(`${baseUrl}/positions`, {
    'headers': { 'X-API-Key': apiKey }
  });
  
  return JSON.parse(response.getContentText());
}
```

### Write to Google Sheets:
```javascript
function updatePositionsSheet() {
  const positions = getPositions();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Clear existing data
  sheet.clear();
  
  // Headers
  sheet.getRange(1, 1, 1, 4).setValues([
    ['Symbol', 'Position', 'Market Value', 'P&L']
  ]);
  
  // Data
  positions.positions.forEach((pos, index) => {
    sheet.getRange(index + 2, 1, 1, 4).setValues([[
      pos.ticker,
      pos.position,
      pos.mktValue,
      pos.unrealizedPnl
    ]]);
  });
}
```

## 🔧 Alternative Deployment Options

| Platform | Free Tier | Pros | Cons |
|----------|-----------|------|------|
| **Render** | 750 hrs/month | Easy setup, Docker | Sleep after 15min idle |
| **Railway** | $5 credit | Fast deployment | Limited free tier |
| **Fly.io** | 3 apps free | Global edge | Complex CLI |

## ⚙️ Configuration Files

- `config.json` - IBKR OAuth credentials (gitignored)
- `api_keys.json` - API access keys (gitignored)  
- `live_trading_oauth_files/` - OAuth certificates (gitignored)

## 🛡️ Security

- All sensitive files are in `.gitignore`
- API key authentication required
- OAuth 1.0a for IBKR communication
- HTTPS enforced in production

## 🧪 Testing Commands

After deployment, test these endpoints:

```bash
# Health check
curl -H "X-API-Key: YOUR_API_KEY_HERE" https://your-app.onrender.com/health

# Account info  
curl -H "X-API-Key: YOUR_API_KEY_HERE" https://your-app.onrender.com/account

# Positions
curl -H "X-API-Key: YOUR_API_KEY_HERE" https://your-app.onrender.com/positions
```

---

**🚀 Ready to deploy!** Your API is now ready for production deployment.
