# IBKR REST API

A RESTful API wrapper for Interactive Brokers (IBKR) using the IBIND library.

## Features

- 🔒 Secure OAuth 1.0a authentication
- 📊 Support for both paper and live trading environments
- 🔄 Real-time market data and order management
- 📈 Support for various order types (market, limit, percentage-based)
- 🎯 Position and portfolio management
- 🔍 Advanced market data queries
- 🛡️ Rate limiting and error handling
- 📝 Comprehensive logging

## Prerequisites

- Python 3.8 or higher
- IBKR Account (paper or live)
- IBKR API credentials
- Docker (optional, for containerized deployment)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ibkr-ibind-rest-api.git
   cd ibkr-ibind-rest-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment:
   - Copy the example configuration file:
     ```bash
     cp config.json.example config.json
     ```
   - Edit `config.json` with your IBKR credentials and settings
   - Place your OAuth key files in the appropriate directories:
     - `paper_trading_oauth_files/` for paper trading
     - `live_trading_oauth_files/` for live trading

5. Start the API server:
   ```bash
   python api.py
   ```

   Or using Docker:
   ```bash
   docker compose up -d
   ```

## Configuration

The application uses a single `config.json` file for all configuration settings:

```json
{
  "paper_trading": {
    "oauth": {
      "consumer_key": "your_consumer_key",
      "access_token": "your_access_token",
      "access_token_secret": "your_access_token_secret",
      "dh_prime": "your_dh_prime",
      "encryption_key_path": "paper_trading_oauth_files/private_encryption.pem",
      "signature_key_path": "paper_trading_oauth_files/private_signature.pem",
      "realm": "limited_poa"
    },
    "api": {
      "host": "https://www.ibkrstaging.com/",
      "api_base": "https://www.ibkrstaging.com/v1/api"
    }
  },
  "live_trading": {
    "oauth": {
      // Similar structure as paper_trading
    },
    "api": {
      "host": "https://api.ibkr.com/",
      "api_base": "https://api.ibkr.com/v1/api"
    }
  },
  "application": {
    "log_level": "INFO",
    "cache_timeout": 300,
    "auto_refresh": true
  }
}
```

### Environment Variables

While most configuration is handled through `config.json`, some runtime settings can be controlled via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `IBIND_TRADING_ENV` | Trading environment (paper/live) | paper_trading |
| `IBIND_ACCOUNT_ID` | Your IBKR account ID | None |

## API Endpoints

### Health Check
```http
GET /health
```

### Switch Environment
```http
POST /switch-environment
Content-Type: application/json

{
  "environment": "paper_trading"  // or "live_trading"
}
```

### Market Data
```http
GET /market-data/{symbol}
GET /market-data/{symbol}/history
```

### Orders
```http
GET /orders
GET /order/{order_id}
POST /order
POST /percentage-limit-order/{symbol}
```

### Positions
```http
GET /positions
GET /position/{symbol}
```

### Portfolio
```http
GET /portfolio
GET /portfolio/ledger
```

## Security Best Practices

1. **Credential Management**
   - Store credentials securely in production environments
   - Use environment variables for sensitive data
   - Never commit credentials to version control

2. **Environment Separation**
   - Use separate credentials for paper and live trading
   - Keep OAuth keys in secure locations
   - Use different API endpoints for paper and live environments

3. **Rate Limiting**
   - The API implements rate limiting to prevent abuse
   - Monitor your API usage to stay within limits

## Troubleshooting

1. **Connection Issues**
   - Verify your network connection
   - Check IBKR API status
   - Ensure credentials are correct

2. **Authentication Errors**
   - Verify OAuth credentials
   - Check key file permissions
   - Ensure correct environment is selected

3. **Order Issues**
   - Verify market hours
   - Check order parameters
   - Review error messages

## Production Deployment

1. **Docker Deployment**
   ```bash
   docker compose up -d
   ```

2. **Environment Setup**
   - Set appropriate environment variables
   - Configure logging
   - Set up monitoring

3. **Security Considerations**
   - Use HTTPS
   - Implement proper authentication
   - Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the documentation
2. Review existing issues
3. Create a new issue if needed
