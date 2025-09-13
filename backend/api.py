#!/usr/bin/env python3
"""
IBKR REST API - Lightweight Route Definitions

A Flask-based REST API for Interactive Brokers (IBKR) trading operations.
This module contains only route definitions - all business logic has been
moved to dedicated modules for better maintainability.
"""

import datetime
import logging
import os
import uuid
from typing import Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ibind import QuestionType, make_order_request

# Import our modular components
from .auth import generate_api_key, require_api_key
from .utils import get_ibkr_client, reset_ibkr_client
from .health_monitor import (
    get_cached_health_status, 
    start_health_monitor, 
    create_health_sse_response
)
from .market_data import get_market_data_for_conids, get_current_price_for_symbol, MarketDataError
from .data_export import generate_positions_csv, get_positions_with_limit
from .account_operations import (
    get_complete_account_data, 
    get_live_orders, 
    get_order_details,
    fetch_all_positions_paginated
)
from .trading_operations import (
    resolve_symbol_to_conid,
    calculate_limit_price,
    find_position_by_symbol,
    calculate_sell_quantity,
    calculate_buy_quantity,
    place_percentage_order,
    validate_percentage_order_request,
    SymbolResolutionError,
    PositionNotFoundError
)

# Add GitHub API integration
import requests
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variable to track the trading environment
TRADING_ENV = os.getenv("IBIND_TRADING_ENV", "live_trading")

# Constants
VALID_TIME_IN_FORCE = ["DAY", "GTC", "IOC", "FOK"]

# Defer IBKR client initialization to runtime usage/startup hooks
logger.info(f"IBKR client will initialize lazily for environment: {TRADING_ENV}")


# ========================
# SYMBOL RESOLUTION ENDPOINT  
# ========================

@app.route("/resolve/<symbol>", methods=["GET"])
@limiter.limit("30 per minute")
@require_api_key
def resolve_symbol(symbol):
    """Resolve a stock symbol to contract ID."""
    client = get_ibkr_client()
    if not client:
        return jsonify({
            "status": "error", 
            "message": "IBKR client not available."
        }), 500

    try:
        conid = resolve_symbol_to_conid(client, symbol.upper())
        return jsonify({
            "status": "success",
            "symbol": symbol.upper(),
            "conid": conid
        })
    except SymbolResolutionError as e:
        logger.error(f"Symbol resolution failed for {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Could not resolve symbol {symbol}: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error resolving {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Unexpected error: {str(e)}"
        }), 500


# =====================
# AUTHENTICATION ROUTES
# =====================

@app.route("/auth", methods=["GET"])
@require_api_key
def auth_check():
    """Authentication check endpoint for Nginx auth_request."""
    return jsonify({"status": "ok"})


@app.route("/generate-api-key", methods=["POST"])
def create_api_key():
    """Generate a new API key (localhost only)."""
    if request.remote_addr not in ["127.0.0.1", "localhost", "::1"]:
        return jsonify({
            "status": "error", 
            "message": "This endpoint can only be accessed locally"
        }), 403

    data = request.json
    name = data.get("name", "Default")

    try:
        api_key = generate_api_key(name)
        return jsonify({"status": "ok", "api_key": api_key})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ================
# HEALTH ENDPOINTS
# ================

@app.route("/health", methods=["GET"])
@limiter.limit("10 per minute")
@require_api_key
def health_check():
    """Lightweight health check endpoint using cached status."""
    try:
        return jsonify(get_cached_health_status())
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "ibkr_connected": False,
            "error": str(e),
            "timestamp": datetime.datetime.now().timestamp()
        }), 500


@app.route("/events/health")
def health_events():
    """Server-Sent Events endpoint for real-time health updates."""
    return create_health_sse_response()


# ====================
# ENVIRONMENT ENDPOINT
# ====================

@app.route("/switch-environment", methods=["POST"])
@limiter.limit("5 per minute")
def switch_environment():
    """Switch between paper and live trading environments."""
    global TRADING_ENV

    data = request.json
    env = data.get("environment")

    if env not in ["paper_trading", "live_trading"]:
        return jsonify({
            "status": "error",
            "message": "Invalid environment. Must be 'paper_trading' or 'live_trading'"
        }), 400

    TRADING_ENV = env
    # Reset client for the previous env and warm up for the new env lazily
    try:
        reset_ibkr_client()
        # Optionally warm up new env
        get_ibkr_client(TRADING_ENV)
        logger.info(f"Switched environment and initialized client for: {TRADING_ENV}")
    except Exception as e:
        logger.warning(f"Environment switched to {TRADING_ENV}, but client init failed: {e}")
    return jsonify({"status": "ok", "environment": TRADING_ENV})


# ==================
# ACCOUNT ENDPOINTS
# ==================

@app.route("/account", methods=["GET"])
@limiter.limit("30 per minute")
@require_api_key
def get_account():
    """Get all account data, including positions and account summary."""
    try:
        account_data = get_complete_account_data()
        return jsonify({
            "status": "ok", 
            "environment": TRADING_ENV, 
            "data": account_data
        })
    except Exception as e:
        logger.error(f"Account data retrieval failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


# ================
# ORDER ENDPOINTS
# ================

@app.route("/orders", methods=["GET"])
@limiter.limit("30 per minute")
@require_api_key
def get_orders():
    """Get all orders for the user."""
    try:
        orders_data = get_live_orders()
        return jsonify({
            "status": "ok",
            "data": orders_data
        })
    except Exception as e:
        logger.error(f"Orders retrieval failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


@app.route("/order/<order_id>", methods=["GET"])
@limiter.limit("30 per minute")
@require_api_key
def get_order(order_id):
    """Get details for a specific order by its ID."""
    try:
        order_details = get_order_details(order_id)
        return jsonify({"data": order_details})
    except Exception as e:
        logger.error(f"Order details retrieval failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


@app.route("/order", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def place_order():
    """Place a single order."""
    client = get_ibkr_client()
    if not client:
        return jsonify({
            "status": "error", 
            "message": "IBKR client not available."
        }), 500

    # Ensure account ID is set
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            return jsonify({
                "status": "error", 
                "message": "No account ID available"
            }), 400

    data = request.json

    # Validate required fields
    required_fields = ["conid", "side", "quantity", "order_type"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    # Validate values
    if data["side"] not in ["BUY", "SELL"]:
        return jsonify({
            "status": "error", 
            "message": "Invalid side. Must be 'BUY' or 'SELL'"
        }), 400

    if data["order_type"] not in ["LMT", "MKT", "STP", "STP_LMT"]:
        return jsonify({
            "status": "error",
            "message": "Invalid order type. Must be one of: LMT, MKT, STP, STP_LMT"
        }), 400

    tif = data.get("tif", "DAY")
    if tif not in VALID_TIME_IN_FORCE:
        return jsonify({
            "status": "error",
            "message": f"Invalid time in force. Must be one of: {', '.join(VALID_TIME_IN_FORCE)}"
        }), 400

    # Create order request
    order_tag = data.get(
        "order_tag", 
        f'order-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    )

    order_request = make_order_request(
        conid=int(data["conid"]),
        side=data["side"],
        quantity=int(data["quantity"]),
        order_type=data["order_type"],
        price=round(float(data["price"]), 2) if "price" in data else None,
        acct_id=client.account_id,
        coid=order_tag,
        tif=tif,
    )

    # Define standard answers
    answers = {
        QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
        QuestionType.ORDER_VALUE_LIMIT: True,
        QuestionType.STOP_ORDER_RISKS: True,
        "Unforeseen new question": True,
        "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True,
        "Market Order Confirmation": True,
        "You are submitting an order without market data. We strongly recommend against this as it may result in erroneous and unexpected trades.Are you sure you want to submit this order?": True,
    }

    try:
        response = client.place_order(order_request, answers).data
        return jsonify({
            "status": "ok", 
            "environment": TRADING_ENV, 
            "data": response, 
            "order_tag": order_tag
        })
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


@app.route("/order/<order_id>", methods=["DELETE"])
@limiter.limit("10 per minute")
@require_api_key
def cancel_order(order_id):
    """Cancel a specific order by its ID."""
    client = get_ibkr_client()
    if not client:
        return jsonify({
            "status": "error", 
            "message": "IBKR client not available."
        }), 500

    try:
        response = client.cancel_order(order_id).data
        return jsonify({
            "status": "ok", 
            "environment": TRADING_ENV, 
            "data": response
        })
    except Exception as e:
        logger.error(f"Order cancellation failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


@app.route("/orders/bulk", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def place_bulk_orders():
    """Place multiple orders in a single request."""
    client = get_ibkr_client()
    if not client or not client.account_id:
        return jsonify({
            "status": "error", 
            "message": "IBKR client not available."
        }), 500

    data = request.get_json()
    if not data or 'orders' not in data or not isinstance(data['orders'], list):
        return jsonify({
            "status": "error", 
            "message": "Invalid bulk order format."
        }), 400

    answers = {
        QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
        QuestionType.ORDER_VALUE_LIMIT: True,
        QuestionType.STOP_ORDER_RISKS: True,
        "Unforeseen new question": True,
        "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True,
        "Market Order Confirmation": True,
        "You are submitting an order without market data. We strongly recommend against this. For more information, see the Order Ticket page in the Learning Center on our website. Are you sure you want to submit this order?": True
    }
    
    responses = []
    errors = []
    
    for order_data in data['orders']:
        try:
            order_request = make_order_request(
                conid=order_data['conid'],
                side=order_data['side'],
                quantity=order_data['quantity'],
                order_type=order_data['order_type'],
                price=order_data.get('price'),
                tif=order_data.get('tif', 'DAY'),
                acct_id=client.account_id,
                coid=f'bulk-trade-{uuid.uuid4()}'
            )
            
            response = client.place_order(order_request, answers=answers).data
            responses.append(response)
            
            # Small delay between orders
            import time
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error processing an order in bulk: {e}")
            errors.append({"order": order_data, "error": str(e)})

    if errors:
        return jsonify({
            "status": "partial_success", 
            "successful_orders": responses, 
            "failed_orders": errors
        }), 207
    
    return jsonify({"status": "ok", "data": responses})


# ======================
# MARKET DATA ENDPOINTS
# ======================

@app.route("/marketdata", methods=["GET"])
@limiter.limit("60 per minute")
@require_api_key
def get_marketdata():
    """Get market data for given contract IDs."""
    conids_str = request.args.get("conids")
    if not conids_str:
        return jsonify({
            "status": "error", 
            "message": "Missing 'conids' parameter"
        }), 400

    # Sanitize and split the conids string
    conid_list = [c.strip() for c in conids_str.split(',') if c.strip().isdigit()]
    if not conid_list:
        return jsonify({
            "status": "error", 
            "message": "Invalid or empty 'conids' parameter"
        }), 400

    try:
        snapshot_data = get_market_data_for_conids(conid_list)
        return jsonify({"status": "ok", "data": snapshot_data})
    except MarketDataError as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


# ==========================
# PERCENTAGE ORDER ENDPOINT
# ==========================

@app.route("/percentage-limit-order/<symbol>", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def percentage_limit_order(symbol):
    """Place a limit order for a percentage of the account value."""
    data = request.json
    side = data.get("side", "SELL").upper()
    time_in_force = data.get("time_in_force", "GTC")

    if side not in ["BUY", "SELL"]:
        return jsonify({
            "status": "error", 
            "message": f"Invalid side: {side}. Must be 'BUY' or 'SELL'"
        }), 400

    try:
        # Validate request data
        validate_percentage_order_request(data, side)
        
        # Resolve symbol to conid
        client = get_ibkr_client()
        conid = resolve_symbol_to_conid(client, symbol)
        
        # Get current market price
        current_price = get_current_price_for_symbol(symbol, conid)
        
        # Calculate limit price
        if side == "SELL":
            percentage = float(data.get("percentage_above_market", 0))
            limit_price = calculate_limit_price(current_price, side, percentage)
        else:  # BUY
            percentage = float(data.get("percentage_below_market", 0))
            limit_price = calculate_limit_price(current_price, side, percentage)

        # Calculate quantity based on side
        if side == "SELL":
            all_positions = fetch_all_positions_paginated()
            position = find_position_by_symbol(all_positions, symbol, conid)
            percentage_of_position = float(data.get("percentage_of_position", 0))
            quantity = calculate_sell_quantity(position, percentage_of_position, symbol)
        else:  # BUY
            dollar_amount = float(data.get("dollar_amount", 0))
            quantity = calculate_buy_quantity(dollar_amount, limit_price)

        # Place the order
        result = place_percentage_order(
            client, symbol, conid, side, quantity, limit_price, time_in_force
        )

        return jsonify({
            "status": "success",
            "message": f"Order placed successfully for {quantity} shares of {symbol} at ${limit_price}",
            "data": result,
        })

    except (SymbolResolutionError, MarketDataError, PositionNotFoundError) as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Percentage order failed for {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Error placing order: {str(e)}"
        }), 500


# ===================
# POSITION ENDPOINTS
# ===================

@app.route("/positions/csv", methods=["GET"])
@limiter.limit("10 per minute")
@require_api_key
def get_positions_csv():
    """Returns a CSV file of all positions."""
    try:
        return generate_positions_csv()
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


@app.route("/positions", methods=["GET"])
@limiter.limit("20 per minute")
@require_api_key
def get_positions():
    """Returns positions in JSON format with optional limit."""
    limit = request.args.get("limit", 10, type=int)
    
    try:
        positions_data = get_positions_with_limit(limit)
        return jsonify({
            "status": "ok",
            "environment": TRADING_ENV,
            **positions_data
        })
    except Exception as e:
        logger.error(f"Positions retrieval failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500


# =======================
# SIMPLE ORDER ENDPOINT
# =======================

@app.route("/api/place_order", methods=["POST"])
@limiter.limit("20 per minute")
@require_api_key
def place_simple_order():
    """Place a simple order using symbol (requires API key authentication)."""
    client = get_ibkr_client()
    if not client:
        return jsonify({
            "status": "error", 
            "message": "IBKR client not available."
        }), 500

    # Ensure account ID is set
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            return jsonify({
                "status": "error", 
                "message": "No account ID available"
            }), 400

    data = request.json

    # Validate required fields
    required_fields = ["symbol", "action", "quantity", "order_type"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    symbol = data["symbol"].upper()
    action = data["action"].upper()
    quantity = int(data["quantity"])
    order_type = data["order_type"].upper()

    # Validate values
    if action not in ["BUY", "SELL"]:
        return jsonify({
            "status": "error", 
            "message": "Invalid action. Must be 'BUY' or 'SELL'"
        }), 400

    if order_type not in ["LMT", "MKT"]:
        return jsonify({
            "status": "error",
            "message": "Invalid order type. Must be 'LMT' or 'MKT'"
        }), 400

    try:
        # Resolve symbol to contract ID
        logger.info(f"Resolving symbol {symbol} to contract ID")
        conid = resolve_symbol_to_conid(client, symbol)
        logger.info(f"Resolved {symbol} to conid: {conid}")

        # Create order request
        order_tag = f'simple-{symbol}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

        order_request = make_order_request(
            conid=int(conid),
            side=action,
            quantity=quantity,
            order_type=order_type,
            price=(round(float(data["limit_price"]), 2) if order_type == "LMT" and "limit_price" in data else None),
            acct_id=client.account_id,
            coid=order_tag,
            tif="DAY",
        )
        if order_type == "LMT" and "limit_price" in data:
            logger.info(f"Setting limit price to ${round(float(data['limit_price']), 2)}")

        # Define standard answers
        answers = {
            QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
            QuestionType.ORDER_VALUE_LIMIT: True,
            QuestionType.STOP_ORDER_RISKS: True,
            "Unforeseen new question": True,
            "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True,
            "Market Order Confirmation": True,
            "You are submitting an order without market data. We strongly recommend against this as it may result in erroneous and unexpected trades.Are you sure you want to submit this order?": True,
        }

        logger.info(f"Placing order for {quantity} shares of {symbol} ({action}) at ${order_request.price if hasattr(order_request, 'price') else 'market'}")
        response = client.place_order(order_request, answers).data
        
        return jsonify({
            "status": "success", 
            "message": f"Order placed successfully for {quantity} shares of {symbol}",
            "order_id": response.get("order_id") if response else None,
            "order_tag": order_tag,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "order_type": order_type,
            "data": response
        })
        
    except SymbolResolutionError as e:
        logger.error(f"Symbol resolution failed for {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Could not resolve symbol {symbol}: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Order placement failed for {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Order placement failed: {str(e)}"
        }), 500


# ===================
# GITHUB WORKFLOW INTEGRATION
# ===================

@app.route('/trigger-workflow', methods=['POST'])
@limiter.limit("5 per minute")
@require_api_key
def trigger_github_workflow():
    """
    Secure endpoint to trigger GitHub Actions workflow via repository_dispatch.
    Frontend sends trading parameters, backend validates and triggers GitHub workflow.
    """
    try:
        # Get GitHub configuration from environment or config file
        github_token = os.getenv('GITHUB_TOKEN')
        repo_owner = os.getenv('GITHUB_REPO_OWNER')
        repo_name = os.getenv('GITHUB_REPO_NAME')
        
        # Fallback to config.json if environment variables not set
        if not github_token or not repo_owner or not repo_name:
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    github_config = config.get('github', {})
                    
                    github_token = github_token or github_config.get('token')
                    repo_owner = repo_owner or github_config.get('repo_owner', 'parthchandak02')
                    repo_name = repo_name or github_config.get('repo_name', 'ibkr-ibind-rest-api')
            except Exception as e:
                logger.warning(f"Could not read GitHub config from config.json: {e}")
        
        if not github_token:
            logger.error("GitHub token not configured")
            return jsonify({
                "status": "error",
                "message": "GitHub integration not configured"
            }), 500
        
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body is required"
            }), 400
        
        # Extract and validate trading parameters
        symbol = data.get('symbol', 'AAPL').upper()
        action = data.get('action', 'BUY').upper()
        quantity = data.get('quantity', 1)
        limit_price = data.get('limit_price', 20.00)
        
        # Validate parameters
        if action not in ['BUY', 'SELL']:
            return jsonify({
                "status": "error",
                "message": "Action must be BUY or SELL"
            }), 400
        
        try:
            quantity = int(quantity)
            limit_price = float(limit_price)
            if quantity <= 0 or limit_price <= 0:
                raise ValueError("Values must be positive")
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Quantity must be positive integer, limit_price must be positive number"
            }), 400
        
        # Prepare GitHub repository dispatch payload
        dispatch_payload = {
            "event_type": "trade_trigger",
            "client_payload": {
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "limit_price": limit_price,
                "triggered_by": "frontend_api",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": request.remote_addr
            }
        }
        
        # GitHub API endpoint
        github_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
        
        # Headers for GitHub API
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Triggering GitHub workflow: {symbol} {action} {quantity} @ ${limit_price}")
        
        # Make request to GitHub API
        response = requests.post(
            github_url, 
            headers=headers, 
            json=dispatch_payload,
            timeout=10
        )
        
        if response.status_code == 204:
            # Success - GitHub repository_dispatch returns 204 No Content
            logger.info(f"Successfully triggered GitHub workflow for {symbol} {action}")
            return jsonify({
                "status": "success",
                "message": "Workflow triggered successfully",
                "workflow_params": {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "limit_price": limit_price
                },
                "triggered_at": dispatch_payload["client_payload"]["timestamp"]
            })
        else:
            # GitHub API error
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            logger.error(f"GitHub API error: {response.status_code} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": f"Failed to trigger workflow: {error_msg}"
            }), 502
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error triggering GitHub workflow: {e}")
        return jsonify({
            "status": "error",
            "message": "Network error communicating with GitHub"
        }), 502
    except Exception as e:
        logger.error(f"Unexpected error triggering GitHub workflow: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500


# ===================
# COMPREHENSIVE API INTEGRATION
# ===================

# Import comprehensive API router
from .comprehensive_api import handle_comprehensive_request


@app.route("/api/comprehensive-execute", methods=["POST"])
@require_api_key
def comprehensive_execute():
    """
    🚀 Comprehensive API endpoint for GitHub Actions integration.
    
    This unified endpoint can handle ANY backend operation:
    - Trading operations (buy, sell, rebalance)
    - Portfolio management (view, export)
    - Order management (view, cancel, history)
    - Market data (quotes, prices, history)
    - Account operations (info, positions)
    - Data export (CSV, JSON, Excel)
    
    Expected JSON payload:
    {
        "operation_type": "trading|portfolio|orders|market_data|account|data_export",
        "action": "operation-specific action",
        "symbol": "AAPL",
        "quantity": "1",
        "dry_run": true,
        "environment": "paper|live"
    }
    """
    return handle_comprehensive_request()


# ===================
# CLI COMMANDS REGISTRATION
# ===================

# Register CLI commands with Flask
from .cli import register_cli_commands
register_cli_commands(app)

# ===================
# APP INITIALIZATION
# ===================

if __name__ == "__main__":
    # Initialize background health monitor
    start_health_monitor()
    
    # Run the app
    app.run(
        debug=True, 
        port=int(os.environ.get("PORT", 8080)), 
        host="0.0.0.0"
    )
