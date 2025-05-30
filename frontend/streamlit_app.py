import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import io

# Configuration
API_BASE_URL = "http://127.0.0.1:8080"
API_KEY = st.secrets["api"]["key"]

# Page config with modern settings
st.set_page_config(
    page_title="IBKR Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark theme
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #0E1117 0%, #1E1E1E 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Header */
    .main-header {
        background: linear-gradient(90deg, #00D4AA 0%, #00A693 50%, #008080 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.1);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Modern Cards */
    .metric-card {
        background: linear-gradient(145deg, #1E1E1E 0%, #2A2A2A 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 212, 170, 0.15);
        border-color: #00D4AA;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00D4AA;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #B0B0B0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    /* Status Indicators */
    .status-connected {
        color: #00D4AA;
        font-weight: 600;
    }
    
    .status-disconnected {
        color: #FF6B6B;
        font-weight: 600;
    }
    
    /* Navigation Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1E1E1E 0%, #2A2A2A 100%);
        border-right: 1px solid #333;
    }
    
    /* Data Tables */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #00D4AA, #00A693);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0, 212, 170, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 212, 170, 0.3);
    }
    
    /* Portfolio Chart Container */
    .chart-container {
        background: linear-gradient(145deg, #1E1E1E 0%, #2A2A2A 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin: 1rem 0;
    }
    
    /* Custom Metrics */
    .custom-metric {
        text-align: center;
        padding: 1rem;
    }
    
    .custom-metric .value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #00D4AA, #00A693);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .custom-metric .label {
        font-size: 0.9rem;
        color: #B0B0B0;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Loading Animation */
    .loading-spinner {
        border: 3px solid #333;
        border-top: 3px solid #00D4AA;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Load custom CSS
load_custom_css()

# Custom header
st.markdown("""
<div class="main-header">
    <h1>🚀 IBKR Trading Dashboard</h1>
    <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; margin: 0.5rem 0 0 0;">
        Professional Trading Interface • Real-time Portfolio Management
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    page = st.radio("", [
        "🏠 Overview",
        "💼 Portfolio", 
        "📋 Orders",
        "📊 Market Data",
        "💰 Trading",
        "⚙️ Settings"
    ], label_visibility="collapsed")

def make_api_request(endpoint, method="GET", params=None, json=None):
    """Enhanced API request with loading states"""
    headers = {"X-API-Key": API_KEY}
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"🚨 API Error: {e}")
        return None

def display_overview():
    st.markdown("## 📊 Overview Dashboard")
    
    # Refresh button with modern styling
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Data", key="overview_refresh"):
            st.rerun()
    
    # Get data
    health = make_api_request("health")
    account_data = make_api_request("account")
    
    # Connection status
    ibkr_connected = False
    environment = "Unknown"
    account_id = "Unknown"
    
    if account_data and account_data.get("status") == "ok":
        data = account_data.get("data", {})
        environment = account_data.get("environment", "Unknown")
        account_id = data.get("selected_account", "Unknown")
        ibkr_connected = True
    
    # Status cards using native Streamlit metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_text = "🟢 Connected" if ibkr_connected else "🔴 Disconnected"
        st.metric("🔗 IBKR Status", status_text)
    
    with col2:
        st.metric("🌍 Environment", environment)
    
    with col3:
        st.metric("👤 Account", account_id)
    
    with col4:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("⏰ Last Update", current_time)
    
    # Portfolio summary
    if ibkr_connected and account_data:
        st.markdown("### 💰 Portfolio Summary")
        
        data = account_data.get("data", {})
        positions = data.get("positions", [])
        
        if positions:
            total_value = sum(pos.get("mktValue", 0) for pos in positions if isinstance(pos.get("mktValue"), (int, float)))
            total_pnl = sum(pos.get("unrealizedPnl", 0) for pos in positions if isinstance(pos.get("unrealizedPnl"), (int, float)))
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💵 Total Value", f"${total_value:,.2f}")
            
            with col2:
                pnl_delta = f"${total_pnl:,.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):,.2f}"
                st.metric("📈 Unrealized P&L", f"${total_pnl:,.2f}", delta=pnl_delta)
            
            with col3:
                st.metric("📊 Total Positions", len(positions))
            
            with col4:
                avg_value = total_value / len(positions) if positions else 0
                st.metric("⚖️ Avg Position", f"${avg_value:,.2f}")
            
            # Portfolio visualization
            if len(positions) > 0:
                st.markdown("#### 📊 Portfolio Distribution")
                
                # Calculate accurate portfolio distribution
                # Get all positions with valid market values
                all_positions = []
                for pos in positions:
                    mkt_value = pos.get("mktValue", 0)
                    if isinstance(mkt_value, (int, float)) and mkt_value != 0:
                        all_positions.append({
                            'ticker': pos.get("ticker", "Unknown"),
                            'name': pos.get("name", "Unknown")[:20],  # Truncate long names
                            'mktValue': mkt_value,
                            'absValue': abs(mkt_value)  # For sorting by size
                        })
                
                if all_positions:
                    # Sort by absolute value (largest holdings first)
                    all_positions.sort(key=lambda x: x['absValue'], reverse=True)
                    
                    # Take top 15 positions for readability
                    top_positions = all_positions[:15]
                    remaining_positions = all_positions[15:]
                    
                    # Calculate total portfolio value (all positions)
                    total_portfolio_value = sum(pos['absValue'] for pos in all_positions)
                    
                    # Prepare chart data
                    labels = []
                    values = []
                    colors = []
                    
                    # Add top positions
                    for pos in top_positions:
                        labels.append(f"{pos['ticker']}")
                        values.append(pos['absValue'])
                        # Color coding: green for positive, red for negative
                        colors.append('#00D4AA' if pos['mktValue'] >= 0 else '#FF6B6B')
                    
                    # Add "Others" category if there are remaining positions
                    if remaining_positions:
                        others_value = sum(pos['absValue'] for pos in remaining_positions)
                        labels.append(f"Others ({len(remaining_positions)} positions)")
                        values.append(others_value)
                        colors.append('#888888')
                    
                    # Create enhanced donut chart
                    fig = go.Figure(data=[go.Pie(
                        labels=labels, 
                        values=values, 
                        hole=0.5,
                        textinfo='label+percent',
                        textfont=dict(color='white', size=10),
                        marker=dict(
                            colors=colors,
                            line=dict(color='#1E1E1E', width=2)
                        ),
                        hovertemplate='<b>%{label}</b><br>' +
                                     'Value: $%{value:,.0f}<br>' +
                                     'Percentage: %{percent}<br>' +
                                     '<extra></extra>'
                    )])
                    
                    # Add center text showing total
                    fig.add_annotation(
                        text=f"Total<br>${total_portfolio_value:,.0f}",
                        x=0.5, y=0.5,
                        font_size=16,
                        font_color="white",
                        showarrow=False
                    )
                    
                    fig.update_layout(
                        height=500,
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=1.02,
                            font=dict(size=10)
                        ),
                        title=dict(
                            text=f"Portfolio Distribution (Top {len(top_positions)} of {len(all_positions)} positions)",
                            font=dict(color='white', size=14),
                            x=0.5,
                            y=0.95
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add summary stats below chart
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Top 15 Holdings", f"${sum(values[:-1] if remaining_positions else values):,.0f}")
                    with col2:
                        top_15_pct = (sum(values[:-1] if remaining_positions else values) / total_portfolio_value) * 100
                        st.metric("🎯 Top 15 %", f"{top_15_pct:.1f}%")
                    with col3:
                        if remaining_positions:
                            st.metric("📈 Others", f"${values[-1]:,.0f} ({len(remaining_positions)} pos)")
                        else:
                            st.metric("✅ All Positions", "Displayed")

def display_portfolio():
    st.markdown("## 💼 Portfolio Management")
    
    # Enhanced refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Portfolio", key="portfolio_refresh"):
            st.rerun()
    
    # Loading state
    with st.spinner("Loading portfolio data..."):
        account_data = make_api_request("account")
    
    if not account_data or account_data.get("status") != "ok":
        st.error("🚨 Unable to fetch portfolio data")
        return
        
    data = account_data.get("data", {})
    positions = data.get("positions", [])
    
    if not positions:
        st.warning("📭 No positions found in your portfolio")
        return
    
    # Portfolio metrics using native Streamlit
    total_value = sum(pos.get("mktValue", 0) for pos in positions if isinstance(pos.get("mktValue"), (int, float)))
    total_pnl = sum(pos.get("unrealizedPnl", 0) for pos in positions if isinstance(pos.get("unrealizedPnl"), (int, float)))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total Positions", len(positions))
    
    with col2:
        st.metric("💰 Portfolio Value", f"${total_value:,.2f}")
    
    with col3:
        pnl_delta = f"${total_pnl:,.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):,.2f}"
        st.metric("📈 Total P&L", f"${total_pnl:,.2f}", delta=pnl_delta)
    
    # Enhanced data table
    try:
        df = pd.DataFrame(positions)
        display_columns = ["ticker", "name", "position", "mktPrice", "mktValue", "unrealizedPnl", "currency"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            portfolio_df = df[available_columns].copy()
            
            # Add data verification section
            with st.expander("🔍 Data Verification & Top Holdings", expanded=False):
                st.markdown("**Portfolio Data Verification:**")
                
                # Show top 10 holdings by absolute value
                df_sorted = df.copy()
                if "mktValue" in df_sorted.columns:
                    df_sorted["absValue"] = df_sorted["mktValue"].apply(lambda x: abs(x) if isinstance(x, (int, float)) else 0)
                    df_sorted = df_sorted.sort_values("absValue", ascending=False)
                    
                    st.markdown("**📊 Top 10 Holdings by Market Value:**")
                    top_10 = df_sorted.head(10)[["ticker", "mktValue", "position", "unrealizedPnl"]].copy()
                    
                    # Format the values for display
                    if "mktValue" in top_10.columns:
                        top_10["Market Value"] = top_10["mktValue"].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else "N/A")
                    if "unrealizedPnl" in top_10.columns:
                        top_10["P&L"] = top_10["unrealizedPnl"].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else "N/A")
                    if "position" in top_10.columns:
                        top_10["Shares"] = top_10["position"].apply(lambda x: f"{x:,.4f}" if isinstance(x, (int, float)) else "N/A")
                    
                    display_top_10 = top_10[["ticker", "Market Value", "Shares", "P&L"]].rename(columns={"ticker": "Symbol"})
                    st.dataframe(display_top_10, use_container_width=True)
                    
                    # Show summary calculations
                    st.markdown("**🧮 Calculation Verification:**")
                    total_calculated = df_sorted["mktValue"].sum() if "mktValue" in df_sorted.columns else 0
                    total_positive = df_sorted[df_sorted["mktValue"] > 0]["mktValue"].sum() if "mktValue" in df_sorted.columns else 0
                    total_negative = df_sorted[df_sorted["mktValue"] < 0]["mktValue"].sum() if "mktValue" in df_sorted.columns else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Total Portfolio", f"${total_calculated:,.2f}")
                    with col2:
                        st.metric("📈 Long Positions", f"${total_positive:,.2f}")
                    with col3:
                        st.metric("📉 Short Positions", f"${total_negative:,.2f}")
            
            # Format columns for main display
            if "mktPrice" in portfolio_df.columns:
                portfolio_df["mktPrice"] = portfolio_df["mktPrice"].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
            if "mktValue" in portfolio_df.columns:
                portfolio_df["mktValue"] = portfolio_df["mktValue"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
            if "unrealizedPnl" in portfolio_df.columns:
                portfolio_df["unrealizedPnl"] = portfolio_df["unrealizedPnl"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
            if "position" in portfolio_df.columns:
                portfolio_df["position"] = portfolio_df["position"].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A")
            
            column_rename = {
                "ticker": "Symbol",
                "name": "Company Name", 
                "position": "Shares",
                "mktPrice": "Market Price",
                "mktValue": "Market Value",
                "unrealizedPnl": "Unrealized P&L",
                "currency": "Currency"
            }
            portfolio_df = portfolio_df.rename(columns=column_rename)
            
            st.markdown("### 📋 Holdings Details & Trading")
            
            # Create interactive trading table
            st.markdown("#### Interactive Trading Table")
            
            # Table headers
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([1.5, 2, 1, 1, 1.5, 1.5, 0.8, 0.8])
            with header_col1:
                st.markdown("**Symbol**")
            with header_col2:
                st.markdown("**Company**")
            with header_col3:
                st.markdown("**Shares**")
            with header_col4:
                st.markdown("**Price**")
            with header_col5:
                st.markdown("**Value**")
            with header_col6:
                st.markdown("**P&L**")
            with header_col7:
                st.markdown("**Trade**")
            with header_col8:
                st.markdown("**Trade**")
            
            st.markdown("---")
            
            for idx, position in enumerate(positions[:20]):  # Show first 20 for performance
                ticker = position.get("ticker", "Unknown")
                name = position.get("name", "Unknown")[:30]
                current_position = position.get("position", 0)
                mkt_price = position.get("mktPrice", 0)
                mkt_value = position.get("mktValue", 0)
                unrealized_pnl = position.get("unrealizedPnl", 0)
                currency = position.get("currency", "USD")
                
                # Format values safely
                try:
                    position_str = f"{current_position:.4f}" if isinstance(current_position, (int, float)) else "N/A"
                    price_str = f"${mkt_price:.2f}" if isinstance(mkt_price, (int, float)) else "N/A"
                    value_str = f"${mkt_value:,.2f}" if isinstance(mkt_value, (int, float)) else "N/A"
                    pnl_str = f"${unrealized_pnl:,.2f}" if isinstance(unrealized_pnl, (int, float)) else "N/A"
                except:
                    position_str = price_str = value_str = pnl_str = "N/A"
                
                # Create expandable container for each position
                with st.container():
                    # Main position row
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 2, 1, 1, 1.5, 1.5, 0.8, 0.8])
                    
                    with col1:
                        st.markdown(f"**{ticker}**")
                    with col2:
                        st.markdown(f"<small>{name}</small>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(position_str)
                    with col4:
                        st.markdown(price_str)
                    with col5:
                        st.markdown(value_str)
                    with col6:
                        pnl_color = "🟢" if isinstance(unrealized_pnl, (int, float)) and unrealized_pnl >= 0 else "🔴"
                        st.markdown(f"{pnl_color} {pnl_str}")
                    with col7:
                        buy_btn = st.button("🟢 Buy", key=f"buy_{ticker}_{idx}", type="secondary")
                    with col8:
                        sell_btn = st.button("🔴 Sell", key=f"sell_{ticker}_{idx}", type="secondary")
                    
                    # Inline trading forms
                    if buy_btn or sell_btn:
                        st.markdown("---")
                        
                        with st.container():
                            if buy_btn:
                                st.markdown(f"**🟢 Buy {ticker}**")
                            else:
                                st.markdown(f"**🔴 Sell {ticker}**")
                            
                            # Quick actions
                            quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
                            
                            with quick_col1:
                                if buy_btn:
                                    if st.button(f"📈 Buy 10", key=f"quick_buy_10_{ticker}_{idx}"):
                                        # Quick buy 10 shares
                                        order_data = {
                                            "symbol": ticker,
                                            "side": "BUY", 
                                            "quantity": 10,
                                            "orderType": "MARKET",
                                            "timeInForce": "GTC"
                                        }
                                        result = make_api_request("order", method="POST", json=order_data)
                                        if result:
                                            st.success(f"✅ Market buy order for 10 {ticker} placed!")
                                        else:
                                            st.error("❌ Failed to place order")
                                else:
                                    if isinstance(current_position, (int, float)) and current_position > 0:
                                        if st.button(f"📉 Sell All", key=f"quick_sell_all_{ticker}_{idx}"):
                                            # Quick sell all shares
                                            order_data = {
                                                "symbol": ticker,
                                                "side": "SELL",
                                                "quantity": int(abs(current_position)),
                                                "orderType": "MARKET", 
                                                "timeInForce": "GTC"
                                            }
                                            result = make_api_request("order", method="POST", json=order_data)
                                            if result:
                                                st.success(f"✅ Market sell order for {int(abs(current_position))} {ticker} placed!")
                                            else:
                                                st.error("❌ Failed to place order")
                            
                            with quick_col2:
                                if buy_btn:
                                    if st.button(f"💰 Buy $1000", key=f"quick_buy_1000_{ticker}_{idx}"):
                                        if isinstance(mkt_price, (int, float)) and mkt_price > 0:
                                            qty = int(1000 / mkt_price)
                                            order_data = {
                                                "symbol": ticker,
                                                "side": "BUY",
                                                "quantity": qty,
                                                "orderType": "MARKET",
                                                "timeInForce": "GTC"
                                            }
                                            result = make_api_request("order", method="POST", json=order_data)
                                            if result:
                                                st.success(f"✅ Market buy order for {qty} {ticker} (~$1000) placed!")
                                            else:
                                                st.error("❌ Failed to place order")
                                else:
                                    if isinstance(current_position, (int, float)) and current_position > 0:
                                        half_qty = int(abs(current_position) / 2)
                                        if st.button(f"📊 Sell Half", key=f"quick_sell_half_{ticker}_{idx}"):
                                            order_data = {
                                                "symbol": ticker,
                                                "side": "SELL",
                                                "quantity": half_qty,
                                                "orderType": "MARKET",
                                                "timeInForce": "GTC"
                                            }
                                            result = make_api_request("order", method="POST", json=order_data)
                                            if result:
                                                st.success(f"✅ Market sell order for {half_qty} {ticker} placed!")
                                            else:
                                                st.error("❌ Failed to place order")
                            
                            # Custom order form
                            st.markdown("**Custom Order:**")
                            
                            form_col1, form_col2, form_col3, form_col4 = st.columns(4)
                            
                            with form_col1:
                                if buy_btn:
                                    custom_qty = st.number_input("Quantity", min_value=1, value=10, key=f"qty_buy_{ticker}_{idx}")
                                else:
                                    # Pre-populate with current position for sell
                                    max_sell = int(abs(current_position)) if isinstance(current_position, (int, float)) and current_position > 0 else 1
                                    custom_qty = st.number_input("Quantity", min_value=1, max_value=max_sell, value=max_sell, key=f"qty_sell_{ticker}_{idx}")
                            
                            with form_col2:
                                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], key=f"type_{ticker}_{idx}")
                            
                            with form_col3:
                                if order_type == "LIMIT":
                                    if isinstance(mkt_price, (int, float)):
                                        # Suggest prices slightly better than market
                                        suggested_price = mkt_price * 0.99 if buy_btn else mkt_price * 1.01
                                        limit_price = st.number_input("Limit Price", min_value=0.01, value=float(suggested_price), step=0.01, key=f"price_{ticker}_{idx}")
                                    else:
                                        limit_price = st.number_input("Limit Price", min_value=0.01, value=100.0, step=0.01, key=f"price_{ticker}_{idx}")
                                else:
                                    limit_price = None
                                    st.markdown("Market Price")
                            
                            with form_col4:
                                tif = st.selectbox("Time in Force", ["GTC", "DAY"], index=0, key=f"tif_{ticker}_{idx}")
                            
                            # Submit custom order
                            action = "Buy" if buy_btn else "Sell"
                            side = "BUY" if buy_btn else "SELL"
                            
                            if st.button(f"🚀 Place {action} Order", key=f"submit_{ticker}_{idx}", type="primary"):
                                order_data = {
                                    "symbol": ticker,
                                    "side": side,
                                    "quantity": custom_qty,
                                    "orderType": order_type,
                                    "timeInForce": tif
                                }
                                
                                if order_type == "LIMIT" and limit_price:
                                    order_data["price"] = limit_price
                                
                                result = make_api_request("order", method="POST", json=order_data)
                                if result:
                                    order_details = f"{order_type} {action.lower()} {custom_qty} {ticker}"
                                    if order_type == "LIMIT":
                                        order_details += f" @ ${limit_price:.2f}"
                                    st.success(f"✅ {order_details} order placed successfully!")
                                    st.json(result)
                                else:
                                    st.error("❌ Failed to place order. Check API connection.")
                        
                        st.markdown("---")
            
            # Show message if more than 20 positions
            if len(positions) > 20:
                st.info(f"📊 Showing first 20 of {len(positions)} positions. Use the data table below to see all positions.")
            
            # Traditional table view as backup
            st.markdown("### 📊 Complete Holdings Table")
            st.dataframe(portfolio_df, use_container_width=True, height=400)
            
            # Download button
            csv_data = portfolio_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Portfolio CSV",
                data=csv_data,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"🚨 Error processing portfolio data: {str(e)}")

def display_orders():
    st.markdown("## 📋 Order Management")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Orders", key="orders_refresh"):
            st.rerun()
    
    with st.spinner("Loading orders..."):
        orders_data = make_api_request("orders")
    
    if not orders_data or "data" not in orders_data or "orders" not in orders_data["data"]:
        st.error("🚨 Unable to fetch orders")
        return
    
    orders = orders_data["data"]["orders"]
    
    if not orders:
        st.info("📭 No orders found")
        return
    
    # Order metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Total Orders", len(orders))
    with col2:
        active_orders = len([o for o in orders if o.get("status") == "Submitted"])
        st.metric("🔄 Active Orders", active_orders)
    with col3:
        filled_orders = len([o for o in orders if o.get("remainingQuantity", 1) == 0])
        st.metric("✅ Filled Orders", filled_orders)
    
    # Orders table
    try:
        orders_list = []
        for order in orders:
            orders_list.append({
                "Order ID": order.get("orderId", ""),
                "Symbol": order.get("ticker", ""),
                "Company": order.get("companyName", "")[:30],
                "Side": order.get("side", ""),
                "Quantity": order.get("totalSize", 0),
                "Price": order.get("price", ""),
                "Status": order.get("status", ""),
                "Time in Force": order.get("timeInForce", "")
            })
        
        df = pd.DataFrame(orders_list)
        st.markdown("### 📊 Orders Overview")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"🚨 Error processing orders: {e}")

def display_market_data():
    st.markdown("## 📊 Market Data")
    
    symbol = st.text_input("🔍 Enter Symbol", "AAPL", key="market_symbol").upper()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 Get Quote", key="get_quote"):
            with st.spinner("Fetching quote..."):
                quote = make_api_request(f"market-data/{symbol}")
                if quote:
                    st.json(quote)
                else:
                    st.warning("Market data endpoint not available")
    
    with col2:
        if st.button("🔗 Get Options Chain", key="get_options"):
            with st.spinner("Fetching options..."):
                options = make_api_request(f"options-chain/{symbol}")
                if options:
                    st.json(options)
                else:
                    st.warning("Options chain endpoint not available")

def display_trading():
    st.markdown("## 💰 Trading Interface")
    st.info("📝 **Note:** Advanced trading interface with modern order entry")
    
    with st.form("modern_order_form", clear_on_submit=False):
        st.markdown("### 📋 Place New Order")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("📊 Symbol", value="AAPL", key="trade_symbol").upper()
            side = st.selectbox("📈 Side", ["BUY", "SELL"], key="trade_side")
            quantity = st.number_input("📊 Quantity", min_value=1, value=1, key="trade_qty")
        
        with col2:
            order_type = st.selectbox("📋 Order Type", ["LIMIT", "MARKET"], key="trade_type")
            if order_type == "LIMIT":
                price = st.number_input("💰 Limit Price", min_value=0.01, value=100.0, step=0.01, key="trade_price")
            else:
                price = None
            time_in_force = st.selectbox("⏰ Time in Force", ["GTC", "DAY"], key="trade_tif")
        
        submitted = st.form_submit_button("🚀 Place Order", type="primary")
        
        if submitted:
            if not symbol:
                st.error("🚨 Symbol is required")
            else:
                order_data = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "orderType": order_type,
                    "timeInForce": time_in_force
                }
                
                if order_type == "LIMIT" and price:
                    order_data["price"] = price
                
                with st.spinner("Placing order..."):
                    result = make_api_request("order", method="POST", json=order_data)
                    if result:
                        st.success("✅ Order placed successfully!")
                        st.json(result)
                    else:
                        st.error("🚨 Failed to place order")

def display_settings():
    st.markdown("## ⚙️ Settings & Configuration")
    
    # Environment switching
    st.markdown("### 🌍 Trading Environment")
    
    health_data = make_api_request("health")
    current_env = health_data.get("environment", "Unknown") if health_data else "Unknown"
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Current Environment", current_env)
    
    with st.form("env_form"):
        new_env = st.selectbox(
            "🔄 Switch Environment:",
            ["live_trading", "paper_trading"],
            index=0 if current_env == "live_trading" else 1
        )
        
        switch_submitted = st.form_submit_button("🔄 Switch Environment", type="primary")
        
        if switch_submitted:
            if new_env != current_env:
                with st.spinner("Switching environment..."):
                    result = make_api_request("switch-environment", method="POST", json={"environment": new_env})
                    if result:
                        st.success(f"✅ Environment switched to {new_env}")
                        st.rerun()
                    else:
                        st.error("🚨 Failed to switch environment")
            else:
                st.info("ℹ️ Already using the selected environment")
    
    # System information
    st.markdown("### 🔧 System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("API Base URL", API_BASE_URL)
    
    with col2:
        st.metric("API Key", f"{API_KEY[:20]}...")
    
    if health_data:
        st.markdown("### 📊 Health Status")
        st.json(health_data)

def place_order_for_symbol(ticker, side, quantity, order_type="MARKET", price=None, tif="GTC"):
    """Helper function to place orders using symbol (will look up contract ID)"""
    try:
        # First, try to get contract ID for the symbol
        # For now, we'll use a simplified approach - you may need to add a contract lookup endpoint
        order_data = {
            "symbol": ticker,  # Backend should handle symbol to conid conversion
            "side": side,
            "quantity": quantity,
            "order_type": "MKT" if order_type == "MARKET" else "LMT",
            "tif": tif
        }
        
        if order_type == "LIMIT" and price:
            order_data["price"] = price
        
        result = make_api_request("order", method="POST", json=order_data)
        return result
    except Exception as e:
        st.error(f"Error placing order: {e}")
        return None

# Main navigation logic
page_map = {
    "🏠 Overview": display_overview,
    "💼 Portfolio": display_portfolio,
    "📋 Orders": display_orders,
    "📊 Market Data": display_market_data,
    "💰 Trading": display_trading,
    "⚙️ Settings": display_settings
}

# Execute selected page
if page in page_map:
    page_map[page]()

# Modern footer
st.markdown("""
---
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🚀 <strong>IBKR Trading Dashboard</strong> • Powered by Streamlit & Python</p>
    <p style="font-size: 0.8rem;">Built with ❤️ for professional traders</p>
</div>
""", unsafe_allow_html=True) 