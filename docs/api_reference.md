# 🔧 IBKR Trading Dashboard API Reference

Complete REST API documentation for the IBKR Trading Dashboard backend.

## 🎯 Base Information

- **Base URL**: `http://localhost:8080`
- **Authentication**: API Key via `X-API-Key` header
- **Content Type**: `application/json`
- **Rate Limiting**: 60 requests per minute per IP

## 🔐 Authentication

All API endpoints require authentication via API key:

```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8080/health
```

### Generate API Key
```bash
python3 utils/generate_key.py --name "Trading Dashboard"
```

## 📊 Core Endpoints

### Health & Status

#### `GET /health`
Returns system health and IBKR connection status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-05-30T11:31:32",
  "environment": "live_trading",
  "ibkr_connected": true,
  "account_id": "U14716312",
  "cache_age": 45,
  "version": "1.0.0"
}
```

### Account & Portfolio

#### `GET /account`
Returns complete account information with paginated positions.

**Parameters:**
- `page` (optional): Page number for position pagination (default: 0)
- `limit` (optional): Number of positions per page (default: 100)

**Response:**
```json
{
  "status": "ok",
  "environment": "live_trading",
  "data": {
    "selected_account": "U14716312",
    "positions": [
      {
        "ticker": "AAPL",
        "name": "Apple Inc",
        "position": 10.0,
        "mktPrice": 150.25,
        "mktValue": 1502.50,
        "unrealizedPnl": 25.50,
        "currency": "USD"
      }
    ],
    "pagination": {
      "current_page": 0,
      "total_pages": 2,
      "total_positions": 133,
      "positions_per_page": 100
    }
  }
}
```

#### `GET /positions`
Returns simplified positions summary.

**Parameters:**
- `limit` (optional): Number of positions to return (default: 50)

**Response:**
```json
{
  "status": "ok",
  "data": {
    "positions": [
      {
        "ticker": "MSFT",
        "position": 25.0,
        "mktValue": 8750.00,
        "unrealizedPnl": 125.00
      }
    ],
    "total_count": 133
  }
}
```

### Order Management

#### `GET /orders`
Returns order history and current orders.

**Response:**
```json
{
  "status": "ok",
  "environment": "live_trading",
  "data": {
    "orders": [
      {
        "orderId": "12345678",
        "ticker": "TSLA",
        "companyName": "Tesla Inc",
        "side": "BUY",
        "totalSize": 10,
        "price": 250.00,
        "status": "Submitted",
        "timeInForce": "GTC",
        "remainingQuantity": 10
      }
    ]
  }
}
```

#### `POST /order`
Places a new trading order.

**Request Body:**
```json
{
  "conid": "265598",
  "side": "BUY",
  "quantity": 10,
  "order_type": "LMT",
  "price": 150.00,
  "tif": "GTC",
  "order_tag": "my-order-123"
}
```

**Parameters:**
- `conid` (required): Contract ID for the security
- `side` (required): "BUY" or "SELL"
- `quantity` (required): Number of shares
- `order_type` (required): "MKT", "LMT", "STP", "STP_LMT"
- `price` (optional): Required for limit orders
- `tif` (optional): "GTC", "DAY", "IOC", "FOK" (default: "DAY")
- `order_tag` (optional): Custom order identifier

**Response:**
```json
{
  "status": "ok",
  "environment": "live_trading",
  "data": {
    "orderId": "87654321",
    "status": "Submitted"
  },
  "order_tag": "my-order-123"
}
```

#### `DELETE /order/<order_id>`
Cancels an existing order.

**Response:**
```json
{
  "status": "ok",
  "environment": "live_trading",
  "data": {
    "orderId": "87654321",
    "status": "Cancelled"
  }
}
```

### Environment Management

#### `POST /switch-environment`
Switches between live and paper trading environments.

**Request Body:**
```json
{
  "environment": "paper_trading"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Environment switched to paper_trading",
  "environment": "paper_trading"
}
```

### Market Data

#### `GET /market-data/<symbol>`
Returns real-time market data for a symbol.

**Example:** `GET /market-data/AAPL`

**Response:**
```json
{
  "status": "ok",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "change": 1.25,
    "changePercent": 0.84,
    "volume": 45234567,
    "timestamp": "2025-05-30T15:30:00Z"
  }
}
```

#### `GET /options-chain/<symbol>`
Returns options chain data for a symbol.

**Example:** `GET /options-chain/AAPL`

**Response:**
```json
{
  "status": "ok",
  "data": {
    "symbol": "AAPL",
    "expiration_dates": ["2025-06-20", "2025-07-18"],
    "strikes": [145, 150, 155, 160],
    "options": [
      {
        "strike": 150,
        "expiration": "2025-06-20",
        "call_bid": 5.25,
        "call_ask": 5.50,
        "put_bid": 3.75,
        "put_ask": 4.00
      }
    ]
  }
}
```

## 🚀 Advanced Trading

### Percentage-Based Orders

#### `POST /percentage-limit-order/<symbol>`
Places percentage-based limit orders.

**For SELL orders:**
```json
{
  "side": "SELL",
  "percentage_above_market": 2.5,
  "percentage_of_position": 50.0,
  "time_in_force": "GTC"
}
```

**For BUY orders:**
```json
{
  "side": "BUY",
  "percentage_below_market": 1.5,
  "dollar_amount": 1000.00,
  "time_in_force": "GTC"
}
```

## 🔍 Error Handling

### Error Response Format
```json
{
  "status": "error",
  "message": "Detailed error description",
  "error_code": "INVALID_SYMBOL",
  "timestamp": "2025-05-30T11:31:32Z"
}
```

### Common Error Codes
- `MISSING_API_KEY`: No API key provided
- `INVALID_API_KEY`: Invalid or expired API key
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_SYMBOL`: Symbol not found
- `INSUFFICIENT_FUNDS`: Not enough buying power
- `MARKET_CLOSED`: Trading session closed
- `INVALID_ORDER_TYPE`: Unsupported order type

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (missing/invalid API key)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

## 📝 Rate Limiting

API requests are limited to protect system stability:

- **Global Limit**: 60 requests per minute per IP
- **Order Endpoints**: 10 requests per minute
- **Market Data**: 30 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## 🧪 Testing Examples

### Test API Health
```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8080/health
```

### Get Portfolio Positions
```bash
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8080/account?page=0&limit=10"
```

### Place Market Order
```bash
curl -X POST \
     -H "X-API-Key: YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "conid": "265598",
       "side": "BUY",
       "quantity": 10,
       "order_type": "MKT",
       "tif": "GTC"
     }' \
     http://localhost:8080/order
```

### Place Limit Order
```bash
curl -X POST \
     -H "X-API-Key: YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "conid": "265598",
       "side": "BUY",
       "quantity": 10,
       "order_type": "LMT",
       "price": 150.00,
       "tif": "GTC"
     }' \
     http://localhost:8080/order
```

### Switch to Paper Trading
```bash
curl -X POST \
     -H "X-API-Key: YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"environment": "paper_trading"}' \
     http://localhost:8080/switch-environment
```

## 🔧 Integration Examples

### Python Integration
```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8080"

headers = {"X-API-Key": API_KEY}

# Get portfolio
response = requests.get(f"{BASE_URL}/account", headers=headers)
portfolio = response.json()

# Place order
order_data = {
    "conid": "265598",
    "side": "BUY",
    "quantity": 10,
    "order_type": "MKT",
    "tif": "GTC"
}
response = requests.post(f"{BASE_URL}/order", json=order_data, headers=headers)
order_result = response.json()
```

### JavaScript Integration
```javascript
const API_KEY = 'your-api-key-here';
const BASE_URL = 'http://localhost:8080';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Get portfolio
const portfolio = await fetch(`${BASE_URL}/account`, { headers })
  .then(res => res.json());

// Place order
const orderData = {
  conid: '265598',
  side: 'BUY',
  quantity: 10,
  order_type: 'MKT',
  tif: 'GTC'
};

const orderResult = await fetch(`${BASE_URL}/order`, {
  method: 'POST',
  headers,
  body: JSON.stringify(orderData)
}).then(res => res.json());
```

## 🔐 Security Best Practices

1. **Store API keys securely** - Never commit to version control
2. **Use HTTPS in production** - Encrypt all API communications
3. **Implement IP whitelisting** - Restrict access to known IPs
4. **Monitor rate limits** - Implement proper backoff strategies
5. **Log all trading activity** - Maintain audit trails
6. **Use environment variables** - Keep credentials separate from code

## 📊 Production Deployment

### Environment Variables
```bash
export IBKR_ENVIRONMENT=live_trading
export API_RATE_LIMIT=60
export LOG_LEVEL=INFO
export OAUTH_CERT_PATH=/path/to/certs
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "run_server.py"]
```

---

**📚 For more examples and integration guides, see the [main README](../README.md) and [frontend documentation](frontend_guide.md).** 