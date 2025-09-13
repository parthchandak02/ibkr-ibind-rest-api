# 🎨 Streamlit Trading Dashboard Guide

Professional frontend interface for the IBKR Trading Dashboard built with Streamlit.

## 🎯 Overview

The frontend provides a **modern, professional trading interface** with:
- **🎨 Dark Theme**: Professional trading UI with animations
- **⚡ Real-time Data**: Live portfolio updates every few seconds
- **📊 Interactive Charts**: Accurate portfolio distribution visualization
- **💰 Inline Trading**: Buy/Sell directly from portfolio table
- **🔍 Data Verification**: Built-in accuracy validation tools

## 🚀 Quick Start

```bash
# 1. Ensure backend is running
uv run python run_server.py  # Backend on :8080

# 2. Start frontend
cd frontend
streamlit run streamlit_app.py --server.port 8501

# 3. Access dashboard
open http://localhost:8501
```

## 📁 Frontend Structure

```
frontend/
├── streamlit_app.py          # Main dashboard application
├── .streamlit/
│   ├── config.toml          # Streamlit configuration & dark theme
│   └── secrets.toml         # API key configuration
└── requirements.txt         # Dependencies (merged into root)
```

## 🎛️ Dashboard Pages

### 🏠 Overview Dashboard
**Primary landing page with portfolio summary**

**Features:**
- **Connection Status**: Live IBKR connection monitoring
- **Environment Display**: Live/Paper trading indicator
- **Account Information**: Account ID and last update time
- **Portfolio Summary**: Total value, P&L, position count, average position size
- **Distribution Chart**: Interactive donut chart showing top 15 holdings

**Key Metrics:**
- Total Portfolio Value: $85,009.40
- Total Positions: 133
- Unrealized P&L: Live calculation with color coding
- Average Position Size: Calculated across all holdings

**Chart Features:**
- **Accurate Data**: Based on all 133 positions, not just a sample
- **Top Holdings**: Shows largest 15 positions by market value
- **Others Category**: Combines remaining positions for clarity
- **Color Coding**: Green for long positions, red for short positions
- **Interactive Tooltips**: Hover for detailed values and percentages

### 💼 Portfolio Management
**Advanced portfolio management with inline trading**

**Interactive Trading Table:**
- **Position Details**: Symbol, company name, shares, price, value, P&L
- **Buy/Sell Buttons**: Inline trading for each position
- **Color-coded P&L**: Green for gains, red for losses

**Quick Actions:**
- **🟢 Buy 10**: Market order for 10 shares
- **💰 Buy $1000**: Calculated quantity for $1000 worth
- **🔴 Sell All**: Market order for entire position
- **📊 Sell Half**: Market order for 50% of position

**Custom Order Forms:**
- **Order Types**: Market and Limit orders
- **Smart Defaults**: Pre-populated quantities and suggested prices
- **Price Suggestions**: Limit orders 1% better than market price
- **Time in Force**: GTC (Good Till Cancel) and DAY options
- **Validation**: Real-time form validation and error handling

**Data Verification Section:**
- **Top Holdings**: Expandable section with detailed breakdown
- **Calculation Audit**: Long vs short position totals
- **Accuracy Check**: Verification that totals match IBKR data

### 📋 Order Management
**Comprehensive order tracking and management**

**Order Metrics:**
- **Total Orders**: Complete order count
- **Active Orders**: Currently pending orders
- **Filled Orders**: Completed orders

**Order Details Table:**
- Order ID, Symbol, Company Name
- Side (Buy/Sell), Quantity, Price
- Status, Time in Force
- Real-time status updates

### 📊 Market Data
**Real-time market data lookup**

**Features:**
- **Symbol Search**: Enter any ticker symbol
- **Live Quotes**: Real-time price data
- **Options Chain**: Options data for any symbol
- **Error Handling**: Graceful handling of invalid symbols

### 💰 Trading Interface
**Professional order entry system**

**Order Entry Form:**
- **Symbol Input**: Ticker symbol with validation
- **Side Selection**: Buy/Sell with visual indicators
- **Quantity Input**: Share quantity with validation
- **Order Types**: Market and Limit order support
- **Price Entry**: Limit price for limit orders
- **Time in Force**: GTC/DAY selection
- **Order Confirmation**: Detailed order verification

### ⚙️ Settings & Configuration
**System configuration and monitoring**

**Environment Management:**
- **Current Environment**: Live/Paper trading display
- **Environment Switching**: Toggle between environments
- **Switch Confirmation**: Verification before switching

**System Information:**
- **API Configuration**: Base URL and API key (masked)
- **Health Status**: Complete system health data
- **Connection Monitoring**: Real-time IBKR connection status

## 🎨 Design System

### Color Palette
```css
Primary: #00D4AA (Teal Green)
Background: #0E1117 (Dark Gray)
Secondary: #1E1E1E (Medium Gray)
Text: #FAFAFA (Off White)
Success: #00D4AA (Green)
Error: #FF6B6B (Red)
Warning: #FFA500 (Orange)
```

### Typography
```css
Font Family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif
Headers: 600-700 weight
Body Text: 400 weight
Code/Monospace: 'JetBrains Mono'
```

### UI Components

**Metrics Cards:**
```python
st.metric("Portfolio Value", "$85,009.40", delta="$1,953.84")
```

**Interactive Buttons:**
```python
st.button("🟢 Buy", type="secondary", key=f"buy_{ticker}")
st.button("🚀 Place Order", type="primary")
```

**Data Tables:**
```python
st.dataframe(df, use_container_width=True, height=400)
```

**Charts:**
```python
fig = go.Figure(data=[go.Pie(...)])  # Plotly charts
st.plotly_chart(fig, use_container_width=True)
```

### Responsive Design
- **Column Layouts**: Flexible column systems for different screen sizes
- **Mobile Optimization**: Touch-friendly buttons and inputs
- **Adaptive Charts**: Charts resize based on container width
- **Scrollable Tables**: Horizontal scroll for wide data tables

## 🔧 Technical Implementation

### API Integration
```python
def make_api_request(endpoint, method="GET", params=None, json=None):
    """Enhanced API request with loading states"""
    headers = {"X-API-Key": API_KEY}
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json, timeout=10)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"🚨 API Error: {e}")
        return None
```

### Real-time Updates
```python
# Auto-refresh every 30 seconds
if st.button("🔄 Refresh Data", key="refresh"):
    st.rerun()

# Session state management
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
```

### Order Placement
```python
def place_order_for_symbol(ticker, side, quantity, order_type="MARKET", price=None):
    """Helper function to place orders using symbol"""
    order_data = {
        "symbol": ticker,
        "side": side,
        "quantity": quantity,
        "order_type": "MKT" if order_type == "MARKET" else "LMT",
        "tif": "GTC"
    }
    
    if order_type == "LIMIT" and price:
        order_data["price"] = price
    
    return make_api_request("order", method="POST", json=order_data)
```

### Data Accuracy
```python
# Portfolio distribution calculation
all_positions = []
for pos in positions:
    mkt_value = pos.get("mktValue", 0)
    if isinstance(mkt_value, (int, float)) and mkt_value != 0:
        all_positions.append({
            'ticker': pos.get("ticker", "Unknown"),
            'mktValue': mkt_value,
            'absValue': abs(mkt_value)
        })

# Sort by size and take top 15
all_positions.sort(key=lambda x: x['absValue'], reverse=True)
top_positions = all_positions[:15]
```

## 📊 Performance Optimization

### Efficient Data Handling
- **Pagination**: Backend handles 133+ positions with pagination
- **Caching**: Session state caching for frequently accessed data
- **Lazy Loading**: Charts and tables load only when needed
- **Error Recovery**: Graceful handling of API failures

### User Experience
- **Loading States**: Spinners and progress indicators
- **Error Messages**: Clear, actionable error messages
- **Keyboard Navigation**: Accessible form navigation
- **Touch Optimization**: Mobile-friendly interactions

### Memory Management
- **Data Filtering**: Show only relevant data (top 20 positions in trading table)
- **Component Isolation**: Independent components for better performance
- **State Cleanup**: Proper cleanup of temporary data

## 🔐 Security Features

### API Key Management
```toml
# .streamlit/secrets.toml
[api]
key = "your-secure-api-key-here"
```

### Input Validation
```python
# Quantity validation
if custom_qty <= 0:
    st.error("Quantity must be positive")
    return

# Price validation for limit orders
if order_type == "LIMIT" and not price:
    st.error("Price required for limit orders")
    return
```

### Error Handling
```python
try:
    result = make_api_request("order", method="POST", json=order_data)
    if result:
        st.success("✅ Order placed successfully!")
    else:
        st.error("❌ Failed to place order")
except Exception as e:
    st.error(f"🚨 Error: {e}")
```

## 🎯 Advanced Features

### Smart Trading Logic
```python
# Smart price suggestions
suggested_price = mkt_price * 0.99 if buy_btn else mkt_price * 1.01

# Pre-populated sell quantities
max_sell = int(abs(current_position)) if current_position > 0 else 1
custom_qty = st.number_input("Quantity", max_value=max_sell, value=max_sell)

# Quick action calculations
qty_for_1000 = int(1000 / mkt_price) if mkt_price > 0 else 0
half_position = int(abs(current_position) / 2)
```

### Data Verification
```python
# Real-time calculation verification
total_calculated = df["mktValue"].sum()
total_positive = df[df["mktValue"] > 0]["mktValue"].sum()
total_negative = df[df["mktValue"] < 0]["mktValue"].sum()

# Display verification metrics
st.metric("💰 Total Portfolio", f"${total_calculated:,.2f}")
st.metric("📈 Long Positions", f"${total_positive:,.2f}")
st.metric("📉 Short Positions", f"${total_negative:,.2f}")
```

### Interactive Charts
```python
# Enhanced donut chart with center annotation
fig.add_annotation(
    text=f"Total<br>${total_portfolio_value:,.0f}",
    x=0.5, y=0.5,
    font_size=16,
    font_color="white",
    showarrow=False
)
```

## 🛠️ Development Workflow

### Local Development
```bash
# Terminal 1: Backend
uv run python run_server.py

# Terminal 2: Frontend
streamlit run frontend/streamlit_app.py --server.port 8501 --server.headless true

# Development with auto-reload
streamlit run frontend/streamlit_app.py --server.runOnSave true
```

### Configuration
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#00D4AA"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E1E1E"
textColor = "#FAFAFA"

[server]
port = 8501
headless = true
runOnSave = true
```

### Debugging
```python
# Debug mode
if st.checkbox("Debug Mode"):
    st.write("Session State:", st.session_state)
    st.write("API Response:", api_response)
    st.json(order_data)
```

## 📈 Future Enhancements

### Planned Features
- **WebSocket Integration**: Real-time price updates
- **Advanced Charts**: TradingView integration
- **Portfolio Analytics**: Performance metrics and analysis
- **Risk Management**: Position sizing and risk tools
- **Alert System**: Price and position alerts
- **Mobile App**: Native mobile application

### Technical Improvements
- **State Management**: Redux-like state management
- **Component Library**: Reusable UI components
- **Testing Suite**: Automated testing framework
- **Performance Monitoring**: Real-time performance metrics

## 🤝 Contributing

### Development Setup
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Start development servers**: Backend + Frontend
5. **Test thoroughly**: Verify all functionality
6. **Submit pull request**: With detailed description

### Code Standards
- **PEP 8**: Python code formatting
- **Type Hints**: Use type annotations
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Graceful error management
- **Security**: Secure API key handling

---

**🎨 Ready to trade with style!** The Streamlit frontend provides a professional, feature-rich interface for managing your IBKR portfolio with real-time data and inline trading capabilities. 