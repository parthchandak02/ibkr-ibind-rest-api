# IBKR API Application

A robust REST API application for accessing Interactive Brokers (IBKR) trading services, providing a simple interface for trading and account management.

## Features

- 🔐 Secure OAuth-based authentication with IBKR
- 🔄 Automatic connection management and retry mechanism
- 📊 Support for both paper and live trading environments
- 📈 Complete order management (view, place, cancel)
- 💼 Account information and portfolio tracking
- 🐳 Dockerized deployment for easy setup
- ⚡ Rate limiting and security features
- 📝 Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- IBKR Account with API access enabled
- OAuth credentials from IBKR

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ibind_rest_api
   ```

2. Set up configuration files:
   ```bash
   cp paper_trading.example.json paper_trading.json
   cp live_trading.example.json live_trading.json
   ```

3. Create OAuth directories:
   ```bash
   mkdir -p paper_trading_oauth_files
   mkdir -p live_trading_oauth_files
   ```

4. Place your OAuth key files in the respective directories according to IBKR's documentation.

5. Start the application:
   ```bash
   docker-compose up -d
   ```

The API will be available at [http://localhost:5001](http://localhost:5001)

### Local Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up configuration files and OAuth directories as described above.

4. Set environment variables (optional):
   ```bash
   export IBIND_ACCOUNT_ID=your_account_id
   export IBIND_USE_OAUTH=true
   export IBIND_TRADING_ENV=paper_trading  # or live_trading
   ```

5. Run the API:
   ```bash
   python api.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IBIND_ACCOUNT_ID` | Your IBKR account ID | Auto-detected |
| `IBIND_USE_OAUTH` | Enable OAuth authentication | true |
| `IBIND_TRADING_ENV` | Trading environment (paper/live) | paper_trading |

### Rate Limits

The API implements rate limiting to prevent abuse:

- Default: 200 requests per day, 50 per hour
- Health check: 5 requests per minute
- Account info: 30 requests per minute
- Order operations: 10 requests per minute

## API Endpoints

### Health Check
```http
GET /health
```
Returns the health status of the API and IBKR connection.

### Switch Environment
```http
POST /switch-environment
```
Body:
```json
{
  "environment": "paper_trading"  // or "live_trading"
}
```

### Account Information
```http
GET /account
```
Returns account details, ledger information, and current positions.

### Orders Management
```http
GET /orders
GET /order/{order_id}
POST /order
DELETE /order/{order_id}
```

### Percentage-Based Orders
```http
POST /percentage-limit-order/{symbol}
```
Body:
```json
{
  "side": "SELL",
  "percentage_above_market": 10,
  "percentage_of_position": 10,
  "time_in_force": "GTC"
}
```

## Security Best Practices

1. **OAuth Key Management**
   - Never commit OAuth files to version control
   - Store keys securely in production environments
   - Rotate keys regularly

2. **Environment Separation**
   - Use separate configurations for paper and live trading
   - Keep production credentials secure

3. **API Security**
   - Use HTTPS in production
   - Implement proper authentication
   - Monitor API usage

## Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify IBKR credentials
   - Check network connectivity
   - Ensure OAuth files are properly placed

2. **Order Placement Failures**
   - Validate order parameters
   - Check account permissions
   - Verify market hours

3. **Rate Limiting**
   - Monitor request frequency
   - Implement exponential backoff
   - Contact support if limits are too restrictive

### Logging

Logs are available in the following locations:
- Docker: `docker-compose logs -f`
- Local: Check the console output or log files

## Production Deployment

### Recommended Setup

1. **Reverse Proxy**
   ```nginx
   server {
       listen 443 ssl;
       server_name api.yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Monitoring**
   - Set up health checks
   - Monitor API usage
   - Track error rates

3. **Backup**
   - Regular configuration backups
   - Secure credential storage
   - Disaster recovery plan

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and support:
1. Check the troubleshooting guide
2. Review existing issues
3. Create a new issue with detailed information
