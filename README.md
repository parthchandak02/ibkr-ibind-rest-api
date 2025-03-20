# IBKR API Application

This is a simple REST API application for accessing IBKR trading services.

## Features

- Connection to Interactive Brokers API via OAuth
- Robust retry mechanism and connection handling
- Support for both paper and live trading environments
- Complete order management (view, place, cancel)
- Account information retrieval
- Dockerized deployment for easy setup
- Comprehensive error handling

## Setup

### Configuration Files

Before running the application, you need to set up your configuration files:

1. Copy the example configuration files to create your own:

   ```bash
   cp paper_trading.example.json paper_trading.json
   cp live_trading.example.json live_trading.json
   ```

2. Edit these files with your IBKR credentials:
   - Replace `YOUR_ACCOUNT_ID` with your IBKR account ID
   - Update the OAuth configuration with your credentials from IBKR

3. Create the OAuth directories:

   ```bash
   mkdir -p paper_trading_oauth_files
   mkdir -p live_trading_oauth_files
   ```

4. Place your OAuth key files in these directories according to IBKR's documentation.

### Local Installation

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (optional):

   ```bash
   # Optional: Set the account ID manually (will be detected automatically if not set)
   export IBIND_ACCOUNT_ID=your_account_id
   export IBIND_USE_OAUTH=true  # Use OAuth for authentication
   export IBIND_TRADING_ENV=paper_trading  # or live_trading
   ```

3. Run the API:

   ```bash
   python api.py
   ```

The API will start on [http://localhost:5001](http://localhost:5001)

### Docker Installation

1. Build and start the Docker container:

   ```bash
   docker-compose up -d
   ```

2. The API will be available at [http://localhost:5001](http://localhost:5001)

3. To view logs:

   ```bash
   docker-compose logs -f
   ```

4. To stop the service:

   ```bash
   docker-compose down
   ```

## API Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the API and the IBKR connection.

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

Switches between paper trading and live trading environments.

### Get Account Information

```http
GET /account
```

Returns account information, ledger details, and current positions.

### Get Orders

```http
GET /orders?status=active
```

Query parameters:

- `status`: Filter orders by status (active, inactive, or all). Default is "active".

Returns a list of orders based on the specified status.

### Get Order by ID

```http
GET /order/{order_id}
```

Returns detailed information about a specific order.

### Place Order

```http
POST /order
```

Body:

```json
{
  "conid": "265598",
  "side": "BUY",
  "order_type": "MKT",
  "quantity": 1,
  "price": 100.50  // Required for limit orders
}
```

Places a new order with the specified parameters.

### Cancel Order

```http
DELETE /order/{order_id}
```

Cancels an existing order.

## Authentication

The API uses the OAuth authentication files from the configuration files:

- `paper_trading.json` - For paper trading
- `live_trading.json` - For live trading

These files reference the OAuth key files in the respective directories:

- `paper_trading_oauth_files`
- `live_trading_oauth_files`

The API automatically selects the correct configuration based on the current environment.

## Security Notes

- OAuth keys are loaded from configuration files, not hardcoded
- The API handles authentication transparently
- Sensitive operations include proper error handling

### Important Security Warning

**Never commit sensitive files to version control:**

1. OAuth configuration files
2. Trading account credentials
3. API keys or secrets
4. Private certificates

All sensitive files are automatically excluded via `.gitignore` and `.dockerignore`. When deploying:

1. Manually copy your OAuth files to the deployment environment
2. Consider using environment variables or a secure secrets manager in production
3. Follow IBKR's security best practices for API key management

## Production Deployment

For a robust production deployment, we recommend the following steps:

1. Use a reverse proxy (e.g., Nginx) in front of the API for TLS termination and security
2. Set up proper monitoring and logging
3. Consider using Docker Compose or Kubernetes for orchestration
4. Implement proper backup procedures for configuration files

### Sample Nginx Configuration

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

## Keep-Alive Mechanism

This API implements a robust connection maintenance mechanism:

- Uses IbkrClient's built-in tickler system to keep the connection alive
- Performs automatic health checks to verify connectivity
- Implements retry logic when the connection is lost
- Gradually increases delay between retry attempts to prevent overwhelming the server

The keep-alive functionality is handled transparently in the background, ensuring the API remains responsive even when the IBKR service experiences temporary disruptions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
