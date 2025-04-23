# IBKR REST API

A RESTful API wrapper for Interactive Brokers (IBKR) using the IBIND library, with proper pagination support for large portfolios.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0.2-green)
![IBIND](https://img.shields.io/badge/ibind-0.1.13-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## What is this?

This is a robust REST API that lets you:
- Trade stocks and ETFs through Interactive Brokers
- Switch between paper trading (practice) and live trading
- Place different types of orders (market, limit, etc.)
- Check your account information and orders
- **Retrieve all positions with proper pagination** (supports 100+ positions)
- **Export positions to CSV** for easy analysis

Perfect for:
- Building trading applications
- Automating your trading strategies
- Learning to trade with paper money before going live
- Managing large portfolios with many positions

## Features

- 🔒 Secure OAuth 1.0a authentication
- 📊 Support for both paper and live trading environments
- 🔄 Real-time market data and order management
- 📈 Support for various order types (market, limit, percentage-based)
- 🎯 Position and portfolio management with **full pagination support**
- 📄 **Export positions to CSV** with comprehensive details
- 🔍 Advanced market data queries
- 🛡️ Rate limiting and error handling
- 📝 Comprehensive logging

## Prerequisites

Before you start, make sure you have:
- Python 3.8 or higher installed
- An IBKR account (paper or live)
- Your IBKR API credentials ready
- Docker (optional, if you want to run in a container)

## Quick Start (5 minutes)

1. **Get the code:**
   ```bash
   git clone https://github.com/yourusername/ibkr-ibind-rest-api.git
   cd ibkr-ibind-rest-api
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your settings:**
   Create a `config.json` file with your IBKR credentials (see example below)

4. **Start the server:**

   ### Production Mode (Docker):
   ```bash
   docker compose up -d
   ```

   ### Development Mode:
   ```bash
   python dev.py
   ```

5. **Test it works:**
   ```bash
   curl http://localhost:5001/health
   ```
   You should see: `{"status": "ok", ...}`

## Development Workflow

This project supports two development workflows:

### 1. Direct Flask Development (Fastest)

For rapid development iterations:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload)
python dev.py
```

Changes to your code will be applied automatically without restarting the server.

### 2. Docker with Code Mounting

For development in a containerized environment:

```bash
# Start container with volume mounts
docker compose up -d

# Make changes to your local files
# Restart container to apply changes
docker compose restart ibkr-api
```

## API Endpoints

### Account Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API health and connection status |
| `/account` | GET | Get account information, positions, and ledger |
| `/positions` | GET | Get detailed position information (paginated) |
| `/positions/csv` | GET | Export all positions to CSV file |
| `/switch-environment` | POST | Switch between paper and live trading |

### Order Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orders` | GET | Get all orders for the account |
| `/order/<order_id>` | GET | Get details for a specific order |
| `/order` | POST | Place a new order |
| `/order/<order_id>` | DELETE | Cancel an existing order |
| `/percentage-limit-order/<symbol>` | POST | Place a percentage-based limit order |

## Position Pagination and CSV Export

This API properly handles large portfolios with over 100 positions by implementing pagination:

```bash
# Get the first 10 positions (default)
curl http://localhost:5001/positions

# Get more positions
curl http://localhost:5001/positions?limit=50

# Export all positions to CSV
curl -o positions.csv http://localhost:5001/positions/csv
```

The CSV export includes:
- Symbol and full name
- Position size and cost basis
- Current market price and value
- Unrealized P&L (both $ and %)
- Sector, asset type and exchange information

## Cloud Deployment

### Option 1: Digital Ocean (Recommended)

1. Create a Digital Ocean Droplet with Docker pre-installed
2. Set up a firewall in Digital Ocean:
   ```bash
   # Only allow specific IPs to access your API
   ufw allow from your_ip_address to any port 5001
   ufw enable
   ```
3. Deploy using Docker:
   ```bash
   git clone https://github.com/yourusername/ibkr-ibind-rest-api.git
   cd ibkr-ibind-rest-api
   docker compose up -d
   ```

### Option 2: Heroku

1. Install Heroku CLI
2. Add Heroku-specific files:
   ```bash
   # Create Procfile
   echo "web: docker compose up" > Procfile
   ```
3. Deploy:
   ```bash
   heroku create your-app-name
   heroku container:push web
   heroku container:release web
   ```

### Security Considerations for Public Deployment ⚠️

1. **DO NOT** expose the API publicly without authentication:
   - Set up a reverse proxy (like Nginx) with SSL/TLS
   - Implement API key authentication
   - Use IP whitelisting to restrict access

2. **Required Security Measures:**
   ```nginx
   # Example Nginx configuration
   server {
       listen 443 ssl;
       server_name your.domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           # Only allow specific IPs
           allow your_ip_address;
           deny all;

           # API key check
           if ($http_x_api_key != "your_secret_key") {
               return 403;
           }

           proxy_pass http://localhost:5001;
       }
   }
   ```

3. **Environment Variables:**
   - Store all sensitive data in environment variables
   - Use secrets management service if available
   ```bash
   # Example .env file (DO NOT commit this)
   IBIND_API_KEY=your_secret_key
   IBIND_ALLOWED_IPS=1.2.3.4,5.6.7.8
   ```

## Basic Usage Examples

1. **Check your account:**
   ```bash
   curl http://localhost:5001/account
   ```

2. **Place a market order:**
   ```bash
   curl -X POST http://localhost:5001/order \
     -H "Content-Type: application/json" \
     -d '{
       "conid": "265598",  # AAPL's contract ID
       "side": "BUY",
       "quantity": 1,
       "order_type": "MKT"
     }'
   ```

3. **View your orders:**
   ```bash
   curl http://localhost:5001/orders
   ```

4. **Export positions to CSV:**
   ```bash
   curl -o positions.csv http://localhost:5001/positions/csv
   ```

## Configuration

### Quick Setup (Minimal Configuration)

1. Copy the example configuration file to create your own configuration:

   ```bash
   cp config.example.json config.json
   ```

2. Edit the `config.json` file with your actual IBKR credentials:

   ```json
   {
     "paper_trading": {
       "oauth": {
         "consumer_key": "your_paper_key",
         "access_token": "your_paper_token",
         "access_token_secret": "your_paper_secret",
         "encryption_key_path": "paper_trading_oauth_files/private_encryption.pem",
         "signature_key_path": "paper_trading_oauth_files/private_signature.pem"
       }
     },
     "live_trading": {
       "oauth": {
         "consumer_key": "your_live_key",
         "access_token": "your_live_token",
         "access_token_secret": "your_live_secret",
         "encryption_key_path": "live_trading_oauth_files/private_encryption.pem",
         "signature_key_path": "live_trading_oauth_files/private_signature.pem"
       }
     }
   }
   ```

> **⚠️ SECURITY WARNING**: Never commit your actual `config.json` file with real credentials to version control. The `.gitignore` file is configured to exclude this file, but always verify it's not being tracked before pushing to a repository.


## License

MIT

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgements

- Built with [IBIND](https://github.com/Voyz/ibind) library
- Uses Flask for the REST API framework
