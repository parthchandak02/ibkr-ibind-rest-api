# IBKR REST API

A RESTful API wrapper for Interactive Brokers (IBKR) using the IBIND library, with proper pagination support for large portfolios.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0.2-green)
![IBIND](https://img.shields.io/badge/ibind-0.1.13-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Overview

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
```bash
git clone https://github.com/yourusername/ibkr-rest-api.git
cd ibkr-rest-api
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

### OAuth Authentication

IBKR requires OAuth 1.0a authentication for API access. Follow these steps to set up OAuth:

1. Create directories for OAuth files:

```bash
mkdir -p paper_trading_oauth_files live_trading_oauth_files
```

2. Generate the necessary keys for OAuth authentication:

```bash
# Generate signature key pair
openssl genrsa -out live_trading_oauth_files/private_signature.pem 2048
openssl rsa -in live_trading_oauth_files/private_signature.pem -outform PEM -pubout -out live_trading_oauth_files/public_signature.pem

# Generate encryption key pair
openssl genrsa -out live_trading_oauth_files/private_encryption.pem 2048
openssl rsa -in live_trading_oauth_files/private_encryption.pem -outform PEM -pubout -out live_trading_oauth_files/public_encryption.pem

# Generate Diffie-Hellman parameters
openssl dhparam -out live_trading_oauth_files/dh_param.pem 2048
```

3. Extract the DH prime value from the parameters file:

```bash
openssl dhparam -in live_trading_oauth_files/dh_param.pem -noout -text | grep -A 100 "prime:" | grep -v "prime:" | tr -d '\n\t: ' | tr -d '\\' > live_trading_oauth_files/dh_prime.txt
```

4. If you're using paper trading, repeat steps 2-3 for the paper trading directory.

### Configuration

1. Create a `config.json` file with your IBKR credentials and OAuth configuration:

```json
{
  "paper_trading": {
    "api": {
      "paper_trading_host": "https://www.ibkrstaging.com/",
      "live_trading_host": "https://api.ibkr.com/"
    },
    "oauth": {
      "access_token": "YOUR_PAPER_ACCESS_TOKEN",
      "access_token_secret": "YOUR_PAPER_ACCESS_TOKEN_SECRET",
      "consumer_key": "YOUR_PAPER_CONSUMER_KEY",
      "encryption_key_path": "paper_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "paper_trading_oauth_files/private_signature.pem",
      "dh_prime": "YOUR_PAPER_DH_PRIME_VALUE",
      "realm": "limited_poa"
    }
  },
  "live_trading": {
    "api": {
      "paper_trading_host": "https://www.ibkrstaging.com/",
      "live_trading_host": "https://api.ibkr.com/"
    },
    "oauth": {
      "access_token": "YOUR_LIVE_ACCESS_TOKEN",
      "access_token_secret": "YOUR_LIVE_ACCESS_TOKEN_SECRET",
      "consumer_key": "YOUR_LIVE_CONSUMER_KEY",
      "encryption_key_path": "live_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "live_trading_oauth_files/private_signature.pem",
      "dh_prime": "YOUR_LIVE_DH_PRIME_VALUE",
      "realm": "limited_poa"
    }
  }
}
```

Replace the placeholder values with your actual IBKR credentials. For the DH prime value, copy the contents of the `dh_prime.txt` file generated in the previous step.

**Important Note**: Make sure the DH prime value does not have the prefix "prime:" in it. It should be just the hexadecimal value.

## Running the API

### Using the Run Script

The easiest way to run the API is to use the provided run script:

```bash
python3 run_server.py --env live_trading --port 5001
```

Options:
- `--env`: Trading environment (`paper_trading` or `live_trading`, default: `live_trading`)
- `--port`: Port to run the server on (default: `5001`)
- `--debug`: Run in debug mode

The script will automatically:
1. Set the correct working directory
2. Configure environment variables
3. Verify OAuth key files exist
4. Start the API server

### Using Docker

For production use, it's recommended to use Docker:

```bash
docker-compose up -d
```

This will build and start the Docker container with the API server. The Docker setup includes:

- Proper mounting of configuration and OAuth files
- Environment variable configuration
- Health checks and automatic restarts
- Resource limits to prevent container from using too many resources

#### Environment Variables

You can customize the Docker deployment using environment variables:

1. **Create a .env file**:
   ```bash
   cp .env.example .env
   # Edit the .env file with your preferred settings
   nano .env
   ```

2. **Available environment variables**:
   - `TRADING_ENV`: Trading environment (`paper_trading` or `live_trading`)
   - `PORT`: Port to expose the API on
   - `DEBUG`: Set to `true` for development mode
   - `ACCOUNT_ID`: Specific IBKR account ID (optional)

3. **Override settings on the command line**:
   ```bash
   TRADING_ENV=paper_trading PORT=8080 docker-compose up -d
   ```

## API Endpoints

### Health Check

- `GET /health`: Check if the API is running and connected to IBKR

### Account Management

- `GET /account`: Get account information
- `GET /positions`: Get all positions
- `GET /positions/csv`: Export positions to CSV

### Order Management

- `GET /orders`: Get all orders
- `GET /orders/{order_id}`: Get a specific order
- `POST /orders`: Place a new order
- `DELETE /orders/{order_id}`: Cancel an order
- `POST /orders/percentage-limit`: Place a percentage-based limit order

#### Development Mode:
```bash
python api.py
```

#### Production Mode (Docker):
```bash
docker compose up -d
```

### 6. Test the Connection

```bash
curl http://localhost:5001/health
```

You should see a response like: `{"status": "ok", ...}`

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
