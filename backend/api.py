#!/usr/bin/env python3
"""
IBKR Trading API - Simplified for Local Automation

A minimal Flask-based REST API for Interactive Brokers (IBKR) trading operations.
Designed for local automation and cron jobs - no authentication, CORS, or rate limiting.
"""

import datetime
import logging
import os

from flask import Flask, jsonify, request
from ibind import QuestionType, make_order_request

from .account_operations import (
    fetch_all_positions_paginated,
    get_complete_account_data,
    get_live_orders,
)
from .data_export import generate_positions_csv, get_positions_with_limit
from .market_data import (
    get_current_price_for_symbol,
    get_market_data_for_conids,
)
from .trading_operations import (
    SymbolResolutionError,
    calculate_buy_quantity,
    calculate_buy_quantity_from_percentage,
    calculate_limit_price,
    calculate_sell_quantity,
    find_position_by_symbol,
    place_percentage_order,
    resolve_symbol_to_conid,
    validate_percentage_order_request,
)

# Import our modular components
from .utils import get_ibkr_client

# Initialize Flask app (minimal setup)
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import and register recurring orders blueprint
try:
    from .api_recurring import recurring_bp
    app.register_blueprint(recurring_bp)
    logger.info("Recurring orders blueprint registered successfully")
except ImportError as e:
    logger.warning(f"Could not import recurring orders blueprint: {e}")
    pass

# Global variable to track the trading environment
TRADING_ENV = os.getenv("IBIND_TRADING_ENV", "live_trading")
VALID_TIME_IN_FORCE = ["DAY", "GTC", "IOC", "FOK"]

logger.info(f"IBKR client will initialize lazily for environment: {TRADING_ENV}")


# ================
# HEALTH CHECK
# ================


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check for automation monitoring."""
    try:
        client = get_ibkr_client()
        ibkr_connected = client and client.check_health() if client else False

        return jsonify(
            {
                "status": "healthy" if ibkr_connected else "unhealthy",
                "ibkr_connected": ibkr_connected,
                "timestamp": datetime.datetime.now().isoformat(),
                "environment": TRADING_ENV,
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "ibkr_connected": False,
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            ),
            500,
        )


# ========================
# SYMBOL RESOLUTION
# ========================


@app.route("/resolve/<symbol>", methods=["GET"])
def resolve_symbol(symbol):
    """Resolve a stock symbol to contract ID."""
    client = get_ibkr_client()
    if not client:
        return (
            jsonify({"status": "error", "message": "IBKR client not available."}),
            500,
        )

    try:
        conid = resolve_symbol_to_conid(client, symbol.upper())
        return jsonify({"status": "success", "symbol": symbol.upper(), "conid": conid})
    except SymbolResolutionError as e:
        logger.error(f"Symbol resolution failed for {symbol}: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Could not resolve symbol {symbol}: {str(e)}",
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Unexpected error resolving {symbol}: {e}")
        return (
            jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}),
            500,
        )


# ==================
# ACCOUNT ENDPOINTS
# ==================


@app.route("/account", methods=["GET"])
def get_account():
    """Get all account data, including positions and account summary."""
    try:
        account_data = get_complete_account_data()
        return jsonify(
            {"status": "ok", "environment": TRADING_ENV, "data": account_data}
        )
    except Exception as e:
        logger.error(f"Account data retrieval failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/positions", methods=["GET"])
def get_positions():
    """Returns positions in JSON format with optional limit."""
    limit = request.args.get("limit", 10, type=int)

    try:
        positions_data = get_positions_with_limit(limit)
        return jsonify({"status": "ok", "environment": TRADING_ENV, **positions_data})
    except Exception as e:
        logger.error(f"Positions retrieval failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/positions/csv", methods=["GET"])
def get_positions_csv():
    """Returns a CSV file of all positions."""
    try:
        return generate_positions_csv()
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ================
# ORDER ENDPOINTS
# ================


@app.route("/orders", methods=["GET"])
def get_orders():
    """Get all orders for the user."""
    try:
        orders_data = get_live_orders()
        return jsonify({"status": "ok", "data": orders_data})
    except Exception as e:
        logger.error(f"Orders retrieval failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/order/<order_id>", methods=["DELETE"])
def cancel_order(order_id):
    """Cancel an existing order by order ID."""
    client = get_ibkr_client()
    if not client:
        return (
            jsonify({"status": "error", "message": "IBKR client not available."}),
            500,
        )

    # Ensure account ID is set
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            return (
                jsonify({"status": "error", "message": "No account ID available"}),
                400,
            )

    try:
        # Cancel the order using IBKR client - correct ibind usage
        response = client.cancel_order(order_id, client.account_id)
        logger.info(f"Order {order_id} cancelled successfully")
        
        return jsonify({
            "status": "success",
            "message": f"Order {order_id} cancelled successfully",
            "order_id": order_id,
            "data": response.data
        })
    except Exception as e:
        logger.error(f"Order cancellation failed for {order_id}: {e}")
        return (
            jsonify({
                "status": "error", 
                "message": f"Failed to cancel order {order_id}: {str(e)}"
            }),
            500,
        )


@app.route("/order", methods=["POST"])
def place_order():
    """Place a single order."""
    client = get_ibkr_client()
    if not client:
        return (
            jsonify({"status": "error", "message": "IBKR client not available."}),
            500,
        )

    # Ensure account ID is set
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            return (
                jsonify({"status": "error", "message": "No account ID available"}),
                400,
            )

    data = request.json

    # Validate required fields
    required_fields = ["conid", "side", "quantity", "order_type"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                }
            ),
            400,
        )

    # Validate values
    if data["side"] not in ["BUY", "SELL"]:
        return (
            jsonify(
                {"status": "error", "message": "Invalid side. Must be 'BUY' or 'SELL'"}
            ),
            400,
        )

    if data["order_type"] not in ["LMT", "MKT", "STP", "STP_LMT"]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid order type. Must be one of: LMT, MKT, STP, STP_LMT",
                }
            ),
            400,
        )

    tif = data.get("tif", "DAY")
    if tif not in VALID_TIME_IN_FORCE:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Invalid time in force. Must be one of: {', '.join(VALID_TIME_IN_FORCE)}",
                }
            ),
            400,
        )

    # Create order request
    order_tag = data.get(
        "order_tag", f'auto-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
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

    # Define standard answers for IBKR prompts (based on Voyz ibind examples)
    answers = {
        QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
        QuestionType.ORDER_VALUE_LIMIT: True,
        QuestionType.STOP_ORDER_RISKS: True,
        QuestionType.MISSING_MARKET_DATA: True,
        "Unforeseen new question": True,  # Used in official Voyz examples
    }

    try:
        response = client.place_order(order_request, answers).data
        logger.info(f"Order placed successfully: {order_tag}")
        return jsonify(
            {
                "status": "ok",
                "environment": TRADING_ENV,
                "data": response,
                "order_tag": order_tag,
            }
        )
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/order/symbol", methods=["POST"])
def place_order_by_symbol():
    """Place an order using symbol (automatically resolves to contract ID)."""
    client = get_ibkr_client()
    if not client:
        return (
            jsonify({"status": "error", "message": "IBKR client not available."}),
            500,
        )

    # Ensure account ID is set
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            return (
                jsonify({"status": "error", "message": "No account ID available"}),
                400,
            )

    data = request.json

    # Validate required fields - support both quantity and cash_qty
    symbol = data.get("symbol", "").upper()
    side = data.get("side", "").upper()
    order_type = data.get("order_type", "").upper()
    quantity = data.get("quantity", 0)
    cash_qty = data.get("cash_qty", 0)
    
    # Check basic required fields
    if not symbol or not side or not order_type:
        return (
            jsonify({
                "status": "error",
                "message": "Missing required fields: symbol, side, order_type"
            }),
            400,
        )
    
    # Check that either quantity OR cash_qty is provided
    if not quantity and not cash_qty:
        return (
            jsonify({
                "status": "error",
                "message": "Either 'quantity' (shares) or 'cash_qty' (dollar amount) must be provided"
            }),
            400,
        )
    
    # If both are provided, prefer cash_qty and warn
    if quantity and cash_qty:
        logger.warning(f"Both quantity ({quantity}) and cash_qty ({cash_qty}) provided. Using cash_qty for dollar-based investment.")
        quantity = 0  # Set to 0 when using cash_qty

    # Validate values
    if side not in ["BUY", "SELL"]:
        return (
            jsonify(
                {"status": "error", "message": "Invalid side. Must be 'BUY' or 'SELL'"}
            ),
            400,
        )

    if order_type not in ["LMT", "MKT"]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid order type. Must be 'LMT' or 'MKT'",
                }
            ),
            400,
        )

    try:
        # Resolve symbol to contract ID
        conid = resolve_symbol_to_conid(client, symbol)
        logger.info(f"Resolved {symbol} to conid: {conid}")

        # Create order request
        order_tag = f'auto-{symbol}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

        # Build order request with cash_qty support
        order_params = {
            "conid": int(conid),
            "side": side,
            "order_type": order_type,
            "acct_id": client.account_id,
            "coid": order_tag,
            "tif": data.get("tif", "DAY"),
        }
        
        # Use cash_qty for dollar-based orders, quantity for share-based orders
        if cash_qty:
            order_params["quantity"] = 1  # Set to 1 when using cash_qty (IBKR will override)
            order_params["cash_qty"] = float(cash_qty)
        else:
            order_params["quantity"] = int(quantity)
        
        # Add price for limit orders
        if order_type == "LMT" and "limit_price" in data:
            order_params["price"] = round(float(data["limit_price"]), 2)

        order_request = make_order_request(**order_params)

        # Define standard answers including market order confirmation (based on Voyz ibind examples)
        answers = {
            QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
            QuestionType.ORDER_VALUE_LIMIT: True,
            QuestionType.STOP_ORDER_RISKS: True,
            QuestionType.CASH_QUANTITY: True,  # Accept cash quantity details
            QuestionType.CASH_QUANTITY_ORDER: True,  # Accept cash quantity orders
            QuestionType.MISSING_MARKET_DATA: True,  # Accept missing market data warning
            QuestionType.ORDER_SIZE_LIMIT: True,  # Accept order size limits
            QuestionType.MANDATORY_CAP_PRICE: True,  # Accept mandatory cap price
            "Unforeseen new question": True,  # Used in official Voyz examples
            "Market Order Confirmation": True,  # Accept market order risks
        }

        response = client.place_order(order_request, answers).data

        # Create success message based on order type
        if cash_qty:
            message = f"Order placed successfully for ${cash_qty} of {symbol}"
            result_data = {
                "status": "success",
                "message": message,
                "order_tag": order_tag,
                "symbol": symbol,
                "side": side,
                "cash_qty": cash_qty,
                "order_type": order_type,
                "data": response,
            }
        else:
            message = f"Order placed successfully for {quantity} shares of {symbol}"
            result_data = {
                "status": "success",
                "message": message,
                "order_tag": order_tag,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "data": response,
            }

        return jsonify(result_data)

    except SymbolResolutionError as e:
        logger.error(f"Symbol resolution failed for {symbol}: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Could not resolve symbol {symbol}: {str(e)}",
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Order placement failed for {symbol}: {e}")
        return (
            jsonify(
                {"status": "error", "message": f"Order placement failed: {str(e)}"}
            ),
            500,
        )


@app.route("/percentage-order/<symbol>", methods=["POST"])
def percentage_limit_order(symbol):
    """Place a limit order for a percentage of account value or position."""
    data = request.json
    side = data.get("side", "SELL").upper()
    time_in_force = data.get("time_in_force", "GTC")

    if side not in ["BUY", "SELL"]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Invalid side: {side}. Must be 'BUY' or 'SELL'",
                }
            ),
            400,
        )

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
            if "percentage_of_buying_power" in data:
                from .account_operations import get_complete_account_data

                account_data = get_complete_account_data()

                ledger = account_data.get("ledger", {})
                buying_power = float(
                    ledger.get("BuyingPower", ledger.get("AvailableFunds", 0))
                )

                if buying_power <= 0:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"No buying power available. Current buying power: ${buying_power}",
                            }
                        ),
                        400,
                    )

                percentage_of_buying_power = float(
                    data.get("percentage_of_buying_power", 0)
                )
                quantity = calculate_buy_quantity_from_percentage(
                    buying_power, percentage_of_buying_power, limit_price, symbol
                )
            else:
                dollar_amount = float(data.get("dollar_amount", 0))
                quantity = calculate_buy_quantity(dollar_amount, limit_price)

        # Place the order
        result = place_percentage_order(
            client, symbol, conid, side, quantity, limit_price, time_in_force
        )

        return jsonify(
            {
                "status": "success",
                "message": f"Order placed successfully for {quantity} shares of {symbol} at ${limit_price}",
                "data": result,
            }
        )

        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Percentage order failed for {symbol}: {e}")
        return (
            jsonify({"status": "error", "message": f"Error placing order: {str(e)}"}),
            500,
        )


# ======================
# MARKET DATA ENDPOINTS
# ======================


@app.route("/marketdata", methods=["GET"])
def get_marketdata():
    """Get market data for given contract IDs."""
    conids_str = request.args.get("conids")
    if not conids_str:
        return (
            jsonify({"status": "error", "message": "Missing 'conids' parameter"}),
            400,
        )

    # Sanitize and split the conids string
    conid_list = [c.strip() for c in conids_str.split(",") if c.strip().isdigit()]
    if not conid_list:
        return (
            jsonify(
                {"status": "error", "message": "Invalid or empty 'conids' parameter"}
            ),
            400,
        )

    try:
        snapshot_data = get_market_data_for_conids(conid_list)
        return jsonify({"status": "ok", "data": snapshot_data})
    except MarketDataError as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/market-data/current-price/<symbol>", methods=["GET"])
def get_current_price(symbol):
    """Get current market price for a given symbol."""
    client = get_ibkr_client()
    if not client:
        return (
            jsonify({"status": "error", "message": "IBKR client not available."}),
            500,
        )

    try:
        # Resolve symbol to contract ID
        conid = resolve_symbol_to_conid(client, symbol.upper())
        
        # Get current price
        current_price = get_current_price_for_symbol(symbol.upper(), conid)
        
        return jsonify({
            "status": "success",
            "symbol": symbol.upper(),
            "conid": conid,
            "price": current_price,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except SymbolResolutionError as e:
        return jsonify({
            "status": "error", 
            "message": f"Symbol resolution failed: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Current price retrieval failed for {symbol}: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Price retrieval failed: {str(e)}"
        }), 500


# ===================
# APP INITIALIZATION
# ===================

if __name__ == "__main__":
    # Run the app (minimal setup for local use)
    from .config import Config
    config = Config()
    settings = config.get_settings()
    
    app.run(
        debug=False,  # Turn off debug for automation
        port=settings["api_port"],  # No fallback - config.json required
        host="127.0.0.1",  # Only listen on localhost
    )
