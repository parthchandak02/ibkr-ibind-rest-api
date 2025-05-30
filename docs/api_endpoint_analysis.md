# IBKR REST API Endpoint Analysis

Based on testing the running backend server on port 8080, here are all available endpoints and their response formats:

## Authentication
- **Header Required**: `X-API-Key: YOUR_API_KEY_PLACEHOLDER`

## Available Endpoints

### 1. Health & Status
- **GET /health** - Check system health
- **GET /events/health** - SSE endpoint for real-time health updates
- **GET /auth** - Authentication check
- **POST /generate-api-key** - Generate new API key
- **POST /switch-environment** - Switch trading environment

### 2. Account & Portfolio
- **GET /account** - Returns complete account information including:
  - Account details and summary
  - **ALL position data** (HUGE response with detailed position info)
  - Net liquidity, buying power, etc.
  - Format: `{"environment": "live_trading", "selected_account": "U14716312", ...}`

- **GET /positions** - Returns just the positions array with metadata:
  - Format: `{"environment": "live_trading", "positions": [...], "status": "ok", "summary": {"displayed": 10, "total_available": 100, "timestamp": "2025-05-30T10:29:33.262535"}}`
  - Each position contains: `acctId`, `ticker`, `position`, `mktPrice`, `mktValue`, `avgCost`, `unrealizedPnl`, `name`, `sector`, `sectorGroup`, `assetClass`, etc.

- **GET /positions/csv** - Returns positions in CSV format

### 3. Orders
- **GET /orders** - Returns all orders:
  - Format: `{"data": {"orders": [...], "snapshot": true}, "status": "ok"}`
  - Each order contains: `orderId`, `ticker`, `side`, `totalSize`, `price`, `status`, `orderType`, `companyName`, etc.

- **GET /order/<order_id>** - Get specific order details
- **POST /order** - Place new order
- **DELETE /order/<order_id>** - Cancel order
- **POST /percentage-limit-order/<symbol>** - Place percentage-based limit order

## Key Response Formats

### Position Object Structure:
```json
{
  "acctId": "U14716312",
  "ticker": "TSLA", 
  "name": "TESLA INC",
  "position": 4.7833,
  "avgCost": 248.8229883,
  "avgPrice": 248.8229883,
  "mktPrice": 348.16970825,
  "mktValue": 1665.4,
  "unrealizedPnl": 475.21,
  "realizedPnl": 0.0,
  "assetClass": "STK",
  "currency": "USD",
  "conid": 76792991,
  "sector": "Consumer, Cyclical",
  "sectorGroup": "Auto-Cars/Light Trucks",
  "group": "Auto Manufacturers",
  "type": "COMMON",
  "listingExchange": "NASDAQ",
  "hasOptions": true
}
```

### Order Object Structure:
```json
{
  "orderId": 131441236,
  "account": "U14716312",
  "ticker": "FLCH",
  "companyName": "FRANKLIN FTSE CHINA ETF",
  "side": "SELL",
  "totalSize": 16.0,
  "remainingQuantity": 16.0,
  "filledQuantity": 0.0,
  "price": "25.00",
  "orderType": "Limit",
  "origOrderType": "LIMIT",
  "timeInForce": "GTC",
  "status": "Submitted",
  "order_ccp_status": "Submitted",
  "orderDesc": "Sell 16 FLCH Limit 25.00, GTC",
  "lastExecutionTime": "250319061240",
  "lastExecutionTime_r": 1742364760000,
  "outsideRTH": true,
  "listingExchange": "ARCA",
  "secType": "STK",
  "cashCcy": "USD"
}
```

### Summary Object Structures:

#### Positions Summary:
```json
{
  "summary": {
    "displayed": 10,
    "total_available": 100,
    "timestamp": "2025-05-30T10:29:33.262535"
  }
}
```

#### Health Status:
```json
{
  "status": "healthy",
  "ibkr_connected": true,
  "environment": "live_trading",
  "timestamp": 1748312345.678
}
```

## Missing Endpoints (Not Found):
- `/quote` - Market data quotes
- `/market-data` - Real-time market data
- Options chain data endpoints
- Historical price data endpoints
- Fundamental data endpoints

## Notes for Frontend Development:
1. **Account endpoint** returns EVERYTHING including positions - very large response (~500KB+)
2. **Positions endpoint** is cleaner for portfolio display with pagination info
3. **Orders endpoint** shows both active and historical orders with detailed execution info
4. All responses include environment info ("live_trading")
5. Positions include comprehensive financial data (P&L, costs, values, sector classification)
6. Currency is consistently USD for this account
7. No market data endpoints available - would need to implement separately or use external data source
8. Positions include detailed exchange routing information (not typically needed for UI)
9. Real-time updates available via SSE at `/events/health`
10. Order cancellation uses DELETE method on `/order/<order_id>`

## Error Handling:
- Invalid endpoints return HTML 404 page
- Authentication failures return appropriate HTTP error codes  
- All successful responses include `"status": "ok"`
- Failed operations return error objects with details

## Data Quality Notes:
- Position values are real-time market prices
- Unrealized P&L calculations are automatic
- Order statuses reflect actual IBKR order states
- Exchange routing data is comprehensive but may be excessive for basic UI needs
- Chinese names available for international securities (`chineseName` field)

## Performance Considerations:
- Positions endpoint: ~500KB response for 100+ positions
- Orders endpoint: Variable size based on order history  
- Health endpoint: Lightweight (<1KB)
- Real-time updates via SSE reduce need for polling 