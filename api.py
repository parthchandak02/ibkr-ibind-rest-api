"""
ibind REST API for trading and account management.

This API provides endpoints for:
1. Checking account information
2. Placing orders
3. Checking active, expired, or historical orders
"""
import os
import datetime
import logging
import time
import csv
import io
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ibind import QuestionType
from ibind.client.ibkr_utils import OrderRequest, parse_order_request

from utils import get_ibkr_client

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to track the trading environment
TRADING_ENV = os.getenv("IBIND_TRADING_ENV", "paper_trading")

# Add this constant at the top of the file with other constants
VALID_TIME_IN_FORCE = ['DAY', 'GTC', 'IOC', 'FOK']


@app.route('/health', methods=['GET'])
@limiter.limit("5 per minute")
def health_check():
    """Health check endpoint."""
    try:
        client = get_ibkr_client(TRADING_ENV)
        health = client.check_health()

        # Get position count with proper pagination handling
        # The IBKR API returns up to 100 positions per page
        all_positions = []
        page = 0
        
        while True:
            try:
                # Fetch positions page by page
                response = client.positions(page=page)
                current_page_positions = response.data
                
                if isinstance(current_page_positions, list) and current_page_positions:
                    all_positions.extend(current_page_positions)
                    
                    # If fewer than 100 positions returned, we've reached the last page
                    if len(current_page_positions) < 100:
                        break
                        
                    # Try the next page
                    page += 1
                    time.sleep(0.5)  # Small delay between requests
                else:
                    # No more data or unexpected format
                    break
            except Exception as page_error:
                logger.error(f"Error fetching positions page {page}: {page_error}")
                break
        
        position_info = {
            'total_count': len(all_positions),
            'pages_fetched': page + 1,
            'first_position': all_positions[0] if all_positions else None,
            'last_position': all_positions[-1] if all_positions else None
        }

        return jsonify({
            "status": "ok",
            "position_info": position_info,
            "environment": TRADING_ENV,
            "ibkr_status": health
        })
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/switch-environment', methods=['POST'])
@limiter.limit("5 per minute")
def switch_environment():
    """Switch between paper and live trading environments."""
    global TRADING_ENV

    data = request.json
    env = data.get('environment')

    if env not in ["paper_trading", "live_trading"]:
        return jsonify({
            "status": "error",
            "message": "Invalid environment. Must be 'paper_trading' or 'live_trading'"
        }), 400

    TRADING_ENV = env
    return jsonify({
        "status": "ok",
        "environment": TRADING_ENV
    })


@app.route('/account', methods=['GET'])
@limiter.limit("30 per minute")
def get_account():
    """Get account information."""
    try:
        client = get_ibkr_client(TRADING_ENV)

        if not client.account_id:
            accounts = client.portfolio_accounts().data
            if accounts and len(accounts) > 0:
                client.account_id = accounts[0]['accountId']
            else:
                return jsonify({
                    "status": "error",
                    "message": "No account ID available"
                }), 400

        # Get account information
        account_data = {}
        account_data["accounts"] = client.portfolio_accounts().data
        account_data["selected_account"] = client.account_id

        # Get ledger information
        ledger = client.get_ledger().data
        account_data["ledger"] = ledger

        # Fetch all positions using pagination
        all_positions = []
        page = 0  # Pages start at 0

        print(f"DEBUG: Starting position pagination at page {page}")

        while True:
            try:
                # Call positions method with proper page parameter - an integer
                print(f"DEBUG: Attempting to fetch positions page: {page}")
                logger.info(f"PAGINATION: Attempting to fetch positions page: {page}")
                response = client.positions(page=page)

                # Check if data exists and is a list
                current_page_positions = response.data

                # Log details about the response
                print(f"DEBUG: Response type: {type(response.data)}, {len(current_page_positions) if isinstance(current_page_positions, list) else 'not a list'}")

                if isinstance(current_page_positions, list) and current_page_positions:
                    print(f"DEBUG: Page {page} has {len(current_page_positions)} positions")
                    # Add all positions from this page
                    all_positions.extend(current_page_positions)

                    print(f"DEBUG: Total positions so far: {len(all_positions)}")

                    # The API returns up to 100 items per page
                    # If fewer items returned, we've reached the last page
                    if len(current_page_positions) < 100:
                        print(f"DEBUG: Last page detected - fewer than 100 positions on page {page}")
                        break

                    # If we got exactly 100 positions, try the next page
                    print(f"DEBUG: Got exactly 100 positions on page {page}, checking next page")
                    page += 1
                    time.sleep(0.5)  # Increased delay between requests
                else:
                    # No more data or unexpected format
                    print(f"DEBUG: No positions found on page {page} or unexpected data format")
                    break
            except Exception as page_error:
                print(f"DEBUG ERROR on page {page}: {page_error}")
                break

        print(f"DEBUG SUMMARY: Retrieved total of {len(all_positions)} positions across {page+1} pages")
        account_data["positions"] = all_positions
        account_data["portfolio_summary"] = {
            'total_positions': len(all_positions),
            'timestamp': datetime.datetime.now().isoformat()
        }

        return jsonify({
            "status": "ok",
            "environment": TRADING_ENV,
            "data": account_data
        })
    except Exception as e:
        logger.error("Failed to get account information: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/orders', methods=['GET'])
@limiter.limit("30 per minute")
def get_orders():
    """Get all orders for the user."""
    try:
        client = get_ibkr_client(TRADING_ENV)
        response = client.live_orders()

        # Check if we have a valid response with orders
        if response and hasattr(response, 'data') and isinstance(response.data, dict):
            orders = response.data.get('orders', [])
            return jsonify({
                "status": "ok",
                "data": {
                    "orders": orders,
                    "snapshot": response.data.get('snapshot', False)
                }
            })
        else:
            return jsonify({
                "status": "ok",
                "data": {
                    "orders": [],
                    "snapshot": False
                }
            })

    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/order/<order_id>', methods=['GET'])
@limiter.limit("30 per minute")
def get_order(order_id):
    """Get details for a specific order."""
    try:
        client = get_ibkr_client(TRADING_ENV)
        order_details = client.order_status(order_id).data
        return jsonify({"data": order_details})
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/order', methods=['POST'])
@limiter.limit("10 per minute")
def place_order():
    """
    Place a new order with the IBKR API.

    Required Parameters:
        conid (str): The contract ID for the security to trade
        side (str): The order side - must be either 'BUY' or 'SELL'
        quantity (int): The number of shares to trade
        order_type (str): The type of order - must be one of:
            - 'LMT' (Limit Order)
            - 'MKT' (Market Order)
            - 'STP' (Stop Order)
            - 'STP_LMT' (Stop Limit Order)

    Optional Parameters:
        price (float): Required for limit orders. The limit price for the order
        order_tag (str): A unique identifier for the order. If not provided, one will be generated
        tif (str): Time in Force - must be one of:
            - 'DAY' (Day Order)
            - 'GTC' (Good Till Cancel)
            - 'IOC' (Immediate or Cancel)
            - 'FOK' (Fill or Kill)
            Defaults to 'DAY' if not specified

    Returns:
        JSON response containing:
            - status: 'ok' or 'error'
            - environment: current trading environment
            - data: order details from IBKR
            - order_tag: the unique identifier for the order

    Raises:
        400: If required fields are missing or invalid
        500: If there's an error communicating with IBKR
    """
    try:
        client = get_ibkr_client(TRADING_ENV)

        if not client.account_id:
            accounts = client.portfolio_accounts().data
            if accounts and len(accounts) > 0:
                client.account_id = accounts[0]['accountId']
            else:
                return jsonify({
                    "status": "error",
                    "message": "No account ID available"
                }), 400

        # Get order details from request body
        data = request.json

        # Validate required fields
        required_fields = ['conid', 'side', 'quantity', 'order_type']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Validate side
        if data['side'] not in ['BUY', 'SELL']:
            return jsonify({
                "status": "error",
                "message": "Invalid side. Must be 'BUY' or 'SELL'"
            }), 400

        # Validate order type
        if data['order_type'] not in ['LMT', 'MKT', 'STP', 'STP_LMT']:
            return jsonify({
                "status": "error",
                "message": "Invalid order type. Must be one of: LMT, MKT, STP, STP_LMT"
            }), 400

        # Validate time in force
        tif = data.get('tif', 'DAY')
        if tif not in VALID_TIME_IN_FORCE:
            return jsonify({
                "status": "error",
                "message": f"Invalid time in force. Must be one of: {', '.join(VALID_TIME_IN_FORCE)}"
            }), 400

        # Generate a unique order tag if not provided
        order_tag = data.get('order_tag', f'order-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}')

        # Create the order request
        conid = data['conid']
        side = data['side']
        quantity = data['quantity']
        order_type = data['order_type']

        # Ensure quantity and price have proper types
        quantity = int(quantity)
        if 'price' in data:
            data['price'] = round(float(data['price']), 2)

        order_request = OrderRequest(
            conid=str(conid),  # Convert conid to string to match example
            side=side,
            quantity=quantity,
            order_type=order_type,
            acct_id=client.account_id,
            coid=order_tag,
            tif=tif
        )

        # Log the order request to help debug
        app.logger.info(f"Order request: {order_request.to_dict()}")

        # Add optional price parameters if present
        if 'price' in data:
            order_request.price = data['price']

        # Define answers for common questions
        answers = {
            QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
            QuestionType.ORDER_VALUE_LIMIT: True,
            QuestionType.STOP_ORDER_RISKS: True,
            "Unforeseen new question": True,
            "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True
        }

        # Place the order
        response = client.place_order(order_request, answers).data

        return jsonify({
            "status": "ok",
            "environment": TRADING_ENV,
            "data": response,
            "order_tag": order_tag
        })
    except Exception as e:
        logger.error("Failed to place order: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/order/<order_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def cancel_order(order_id):
    """Cancel an existing order."""
    try:
        client = get_ibkr_client(TRADING_ENV)

        # Cancel the order
        response = client.cancel_order(order_id).data

        return jsonify({
            "status": "ok",
            "environment": TRADING_ENV,
            "data": response
        })
    except Exception as e:
        logger.error("Failed to cancel order: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/percentage-limit-order/<symbol>', methods=['POST'])
@limiter.limit("10 per minute")
def percentage_limit_order(symbol):
    """
    Place a limit order for a specified symbol with flexible parameters:

    For SELL orders:
    - percentage_above_market: Percentage above current market price to set the limit price
    - percentage_of_position: Percentage of current position to sell

    For BUY orders:
    - percentage_below_market: Percentage below current market price to set the limit price
    - dollar_amount: Amount in USD to buy (will calculate quantity based on limit price)

    Common parameters:
    - side: 'BUY' or 'SELL' (defaults to 'SELL')
    - time_in_force: Order validity (e.g., 'GTC', 'DAY')

    Returns:
    - JSON with order details or error message
    """
    client = None
    try:
        client = get_ibkr_client(TRADING_ENV)
        logger.info("Created new IBKR client for request")

        # Parse request data
        data = request.json
        side = data.get('side', 'SELL').upper()
        time_in_force = data.get('time_in_force', 'GTC')

        if side not in ['BUY', 'SELL']:
            return jsonify({
                "status": "error",
                "message": f"Invalid side: {side}. Must be 'BUY' or 'SELL'"
            }), 400

        # Step 1: Get conid for the symbol
        try:
            # First, get all stocks matching the symbol
            stocks_data = client.security_stocks_by_symbol(symbol).data
            if not stocks_data or len(stocks_data) == 0:
                return jsonify({
                    "status": "error",
                    "message": f"No stocks found for symbol: {symbol}"
                }), 404

            # Try to get the conid using stock_conid_by_symbol with preference for US ARCA exchange
            conid = None
            try:
                # Try with default filtering first (usually selects US stocks)
                symbol_info = client.stock_conid_by_symbol(symbol).data
                if symbol_info and 'conid' in symbol_info:
                    conid = str(symbol_info['conid'])
                    logger.info(f"Found conid {conid} for {symbol} using default filtering")
                else:
                    # Default filtering didn't work, try to find a US stock on any major exchange
                    # Define priority order of exchanges to try
                    preferred_exchanges = ['ARCA', 'NYSE', 'NASDAQ', 'BATS', 'ISLAND', 'AMEX']
                    
                    # First try preferred exchanges in order
                    for exchange in preferred_exchanges:
                        if conid:  # If we already found a match, break
                            break
                            
                        for stock_symbol, stock_list in stocks_data.items():
                            for stock in stock_list:
                                if 'contracts' in stock:
                                    for contract in stock['contracts']:
                                        if contract.get('isUS') and contract.get('exchange') == exchange:
                                            conid = str(contract['conid'])
                                            logger.info(f"Selected US {exchange} conid {conid} for {symbol}")
                                            break
                                    if conid:
                                        break
                            if conid:
                                break
                    
                    # If still no match, try any US exchange
                    if not conid:
                        logger.info(f"No match on preferred exchanges, trying any US exchange for {symbol}")
                        for stock_symbol, stock_list in stocks_data.items():
                            for stock in stock_list:
                                if 'contracts' in stock:
                                    for contract in stock['contracts']:
                                        if contract.get('isUS'):
                                            conid = str(contract['conid'])
                                            logger.info(f"Selected US {contract.get('exchange')} conid {conid} for {symbol}")
                                            break
                                    if conid:
                                        break
                            if conid:
                                break

                if not conid:
                    return jsonify({
                        "status": "error",
                        "message": f"Could not determine a suitable conid for {symbol}",
                        "available_stocks": stocks_data
                    }), 400
            except Exception as stock_query_error:
                logger.error(f"Error getting conid for {symbol}: {stock_query_error}")
                return jsonify({
                    "status": "error",
                    "message": f"Could not determine a conid for {symbol}",
                    "error": str(stock_query_error)
                }), 400

        except Exception as e:
            logger.error(f"Error getting conid for symbol {symbol}: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error getting conid for symbol {symbol}: {str(e)}"
            }), 500

        # Step 2: Get current market data
        try:
            market_data = client.marketdata_history_by_conid(conid, period='1d', bar='1d', outside_rth=True).data
            if not market_data or 'data' not in market_data or not market_data['data']:
                return jsonify({
                    "status": "error",
                    "message": f"Could not get current market price for {symbol}"
                }), 500

            # Use the latest data point for the current price
            latest_data = market_data['data'][-1]
            current_price = float(latest_data.get('c', 0))  # 'c' is close price

            if current_price <= 0:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid current price for {symbol}: {current_price}"
                }), 500

            # Calculate limit price based on side and percentage
            if side == 'SELL':
                percentage_above_market = float(data.get('percentage_above_market', 0))
                price_multiplier = 1 + (percentage_above_market / 100)
                limit_price = round(current_price * price_multiplier, 2)
            else:  # BUY
                percentage_below_market = float(data.get('percentage_below_market', 0))
                price_multiplier = 1 - (percentage_below_market / 100)
                limit_price = round(current_price * price_multiplier, 2)

            logger.info(f"Current price: {current_price}, Limit price: {limit_price}")
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error getting market data for {symbol}: {str(e)}"
            }), 500

        # Step 3: Calculate quantity based on side
        try:
            if side == 'SELL':
                # Get all positions with proper pagination handling
                all_positions = []
                page = 0
                
                logger.info(f"Fetching positions with pagination starting at page {page}")
                
                while True:
                    try:
                        # Fetch positions page by page
                        response = client.positions(page=page)
                        current_page_positions = response.data
                        
                        if isinstance(current_page_positions, list) and current_page_positions:
                            logger.info(f"Retrieved {len(current_page_positions)} positions from page {page}")
                            all_positions.extend(current_page_positions)
                            
                            # If fewer than 100 positions returned, we've reached the last page
                            if len(current_page_positions) < 100:
                                break
                                
                            # Try the next page
                            page += 1
                            time.sleep(0.5)  # Small delay between requests
                        else:
                            # No more data or unexpected format
                            break
                    except Exception as page_error:
                        logger.error(f"Error fetching positions page {page}: {page_error}")
                        break
                
                position_data = all_positions
                matching_position = None
                
                # Log the total number of positions found
                logger.info(f"Retrieved a total of {len(position_data)} positions across {page+1} pages")

                # Find the matching position for our conid or ticker
                if position_data:
                    # First try to match by conid
                    for position in position_data:
                        if str(position.get('conid')) == conid:
                            matching_position = position
                            logger.info(f"Found position match by conid: {conid}")
                            break
                    
                    # If no match by conid, try to match by ticker (case insensitive)
                    if not matching_position:
                        logger.info(f"No match by conid, trying to match by ticker: {symbol}")
                        for position in position_data:
                            position_ticker = position.get('ticker', '')
                            if position_ticker and position_ticker.upper() == symbol.upper():
                                matching_position = position
                                logger.info(f"Found position match by ticker: {position_ticker}")
                                break

                if not matching_position:
                    return jsonify({
                        "status": "error",
                        "message": f"No position found for {symbol}"
                    }), 404

                # Calculate quantity based on percentage
                current_position = float(matching_position.get('position', 0))
                if current_position == 0:
                    return jsonify({
                        "status": "error",
                        "message": f"Current position for {symbol} is zero"
                    }), 400

                percentage_of_position = float(data.get('percentage_of_position', 0))
                # Calculate quantity from percentage (round up to nearest integer)
                quantity_float = abs(current_position) * (percentage_of_position / 100)
                quantity = max(1, int(quantity_float + 0.99))  # Round up to nearest integer
                logger.info(f"Calculated quantity {quantity} from {percentage_of_position}% of position {current_position}")
            else:  # BUY
                dollar_amount = float(data.get('dollar_amount', 0))
                if dollar_amount <= 0:
                    return jsonify({
                        "status": "error",
                        "message": "Dollar amount must be greater than 0 for BUY orders"
                    }), 400

                # Calculate quantity based on dollar amount and limit price (round up)
                quantity_float = dollar_amount / limit_price
                quantity = max(1, int(quantity_float + 0.99))  # Round up to nearest integer
                logger.info(f"Calculated quantity {quantity} from ${dollar_amount} at ${limit_price}")

        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error calculating quantity: {str(e)}"
            }), 500

        # Step 4: Place the order
        try:
            # Generate a unique order tag
            order_tag = f'percentage-{symbol}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

            # Create the order request
            from ibind import make_order_request

            order_request = make_order_request(
                conid=conid,
                side=side,
                quantity=quantity,
                order_type='LMT',
                price=limit_price,
                acct_id=client.account_id,
                coid=order_tag,
                tif=time_in_force
            )

            # Log the order request
            logger.info(f"Order request: {order_request}")

            # Define answers for common questions
            answers = {
                QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
                QuestionType.ORDER_VALUE_LIMIT: True,
                QuestionType.MISSING_MARKET_DATA: True,
                QuestionType.STOP_ORDER_RISKS: True,
                "Unforeseen new question": True,
                "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True
            }

            # Place the order
            result = client.place_order(order_request, answers)

            if result.data:
                return jsonify({
                    "status": "success",
                    "message": f"Order placed successfully for {quantity} shares of {symbol} at ${limit_price}",
                    "data": result.data
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Error placing order: {result.error_message}"
                }), 400

        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return jsonify({
                "status": "error",
                "message": f"Error placing order: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"Error in percentage_limit_order endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500
    finally:
        # Clean up: Ensure we properly close the client connection
        if client:
            try:
                client.logout()
                logger.info("Successfully logged out IBKR client")
            except Exception as e:
                logger.error(f"Error logging out IBKR client: {e}")


@app.route('/positions/csv', methods=['GET'])
@limiter.limit("10 per minute")
def get_positions_csv():
    """Export all positions to a CSV file."""
    try:
        client = get_ibkr_client(TRADING_ENV)

        # Fetch all positions using pagination (same logic as in get_account)
        all_positions = []
        page = 0

        print(f"DEBUG: Starting position pagination for CSV export at page {page}")

        while True:
            try:
                response = client.positions(page=page)
                current_page_positions = response.data

                if isinstance(current_page_positions, list) and current_page_positions:
                    print(f"DEBUG: CSV export - Page {page} has {len(current_page_positions)} positions")
                    all_positions.extend(current_page_positions)

                    if len(current_page_positions) < 100:
                        break

                    page += 1
                    time.sleep(0.5)
                else:
                    break
            except Exception as page_error:
                print(f"DEBUG ERROR on CSV export page {page}: {page_error}")
                break

        print(f"DEBUG: CSV export retrieved {len(all_positions)} positions")

        # Sample first position for debugging
        if all_positions:
            first_pos = all_positions[0]
            print(f"DEBUG: First position sample data:")
            for key in first_pos.keys():
                print(f"  {key}: {first_pos.get(key)}")

        # Create CSV data
        output = io.StringIO()
        fieldnames = [
            'Symbol', 'Name', 'Position', 'Avg Cost', 'Market Price',
            'Market Value', 'Cost Basis', 'Unrealized P&L', 'P&L %',
            'Currency', 'Sector', 'Type', 'Country', 'Exchange'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write positions to CSV with enhanced formatting
        for position in all_positions:
            # Extract numerical values safely
            position_qty = float(position.get('position', 0) or 0)
            avg_cost = float(position.get('avgPrice', 0) or 0)
            market_price = float(position.get('mktPrice', 0) or 0)
            market_value = float(position.get('mktValue', 0) or 0)
            unrealized_pnl = float(position.get('unrealizedPnl', 0) or 0)

            # Calculate P&L percentage if we have valid prices
            if avg_cost > 0 and market_price > 0:
                pnl_percent = ((market_price - avg_cost) / avg_cost) * 100
            else:
                pnl_percent = 0

            # Calculate cost basis
            cost_basis = position_qty * avg_cost

            # Get symbol - try different fields that might contain it
            symbol = position.get('ticker', '') or position.get('contractDesc', '') or position.get('symbol', '')

            # Format row with readable column names
            row = {
                'Symbol': symbol,
                'Name': position.get('name', ''),
                'Position': f"{position_qty:,.2f}",
                'Avg Cost': f"${avg_cost:,.2f}",
                'Market Price': f"${market_price:,.2f}",
                'Market Value': f"${market_value:,.2f}",
                'Cost Basis': f"${cost_basis:,.2f}",
                'Unrealized P&L': f"${unrealized_pnl:,.2f}",
                'P&L %': f"{pnl_percent:.2f}%",
                'Currency': position.get('currency', ''),
                'Sector': position.get('sector', ''),
                'Type': position.get('type', ''),
                'Country': position.get('countryCode', ''),
                'Exchange': position.get('listingExchange', '')
            }
            writer.writerow(row)

        # Prepare the response
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=positions_{timestamp}.csv',
                'Content-Type': 'text/csv'
            }
        )
        return response

    except Exception as e:
        logger.error("Failed to generate positions CSV: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/positions', methods=['GET'])
@limiter.limit("20 per minute")
def get_positions():
    """Get detailed position information."""
    try:
        client = get_ibkr_client(TRADING_ENV)

        # Get limit parameter (default to 10)
        limit = request.args.get('limit', 10, type=int)

        # Fetch positions with pagination
        all_positions = []
        page = 0

        while True:
            try:
                response = client.positions(page=page)
                current_page_positions = response.data

                if isinstance(current_page_positions, list) and current_page_positions:
                    all_positions.extend(current_page_positions)

                    # Break if we have enough positions or reached the last page
                    if len(all_positions) >= limit or len(current_page_positions) < 100:
                        break

                    page += 1
                    time.sleep(0.5)
                else:
                    break
            except Exception as page_error:
                print(f"Error on page {page}: {page_error}")
                break

        # Return only the requested number of positions
        positions_to_return = all_positions[:limit]

        # Add summary information
        position_summary = {
            'total_available': len(all_positions),
            'displayed': len(positions_to_return),
            'timestamp': datetime.datetime.now().isoformat()
        }

        return jsonify({
            "status": "ok",
            "environment": TRADING_ENV,
            "summary": position_summary,
            "positions": positions_to_return
        })
    except Exception as e:
        logger.error("Failed to get positions: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
