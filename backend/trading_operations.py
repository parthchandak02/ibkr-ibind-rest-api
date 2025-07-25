"""
Trading Operations Module

This module contains refactored trading operations that were previously
embedded in large API route functions. Each function has a single responsibility
and can be tested independently.
"""

import datetime
import logging
import time
from typing import Any, Dict, List, Optional

from ibind import IbkrClient, make_order_request
from ibind import QuestionType

logger = logging.getLogger(__name__)


class SymbolResolutionError(Exception):
    """Raised when a symbol cannot be resolved to a contract ID."""

    pass


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved."""

    pass


class PositionNotFoundError(Exception):
    """Raised when a position is not found for a symbol."""

    pass


def resolve_symbol_to_conid(client: IbkrClient, symbol: str) -> str:
    """
    Resolve a stock symbol to a contract ID (conid).

    Args:
        client: Authenticated IBKR client
        symbol: Stock symbol to resolve

    Returns:
        str: Contract ID for the symbol

    Raises:
        SymbolResolutionError: If symbol cannot be resolved
    """
    try:
        # First, get all stocks matching the symbol
        stocks_data = client.security_stocks_by_symbol(symbol).data
        if not stocks_data or len(stocks_data) == 0:
            raise SymbolResolutionError(f"No stocks found for symbol: {symbol}")

        # Try to get the conid using stock_conid_by_symbol with preference for US exchanges
        conid = None

        try:
            # Try with default filtering first (usually selects US stocks)
            symbol_info = client.stock_conid_by_symbol(symbol).data
            if symbol_info and "conid" in symbol_info:
                conid = str(symbol_info["conid"])
                logger.info(f"Found conid {conid} for {symbol} using default filtering")
                return conid
        except Exception as e:
            logger.warning(f"Default symbol resolution failed for {symbol}: {e}")

        # Default filtering didn't work, try to find a US stock on preferred exchanges
        preferred_exchanges = ["ARCA", "NYSE", "NASDAQ", "BATS", "ISLAND", "AMEX"]

        # First try preferred exchanges in order
        for exchange in preferred_exchanges:
            if conid:  # If we already found a match, break
                break

            for stock_symbol, stock_list in stocks_data.items():
                for stock in stock_list:
                    if "contracts" in stock:
                        for contract in stock["contracts"]:
                            if contract.get("isUS") and contract.get("exchange") == exchange:
                                conid = str(contract["conid"])
                                logger.info(f"Selected US {exchange} conid {conid} for {symbol}")
                                return conid

        # If still no match, try any US exchange
        if not conid:
            logger.info(f"No match on preferred exchanges, trying any US exchange for {symbol}")
            for stock_symbol, stock_list in stocks_data.items():
                for stock in stock_list:
                    if "contracts" in stock:
                        for contract in stock["contracts"]:
                            if contract.get("isUS"):
                                conid = str(contract["conid"])
                                logger.info(
                                    f"Selected US {contract.get('exchange')} conid {conid} for {symbol}"
                                )
                                return conid

        if not conid:
            raise SymbolResolutionError(
                f"Could not determine a suitable conid for {symbol}. "
                f"Available stocks: {stocks_data}"
            )

        return conid

    except Exception as e:
        if isinstance(e, SymbolResolutionError):
            raise
        raise SymbolResolutionError(f"Error resolving symbol {symbol}: {str(e)}")


def get_current_market_price(client: IbkrClient, conid: str, symbol: str) -> float:
    """
    Get the current market price for a contract.

    Args:
        client: Authenticated IBKR client
        conid: Contract ID
        symbol: Symbol for error messages

    Returns:
        float: Current market price

    Raises:
        MarketDataError: If market data cannot be retrieved
    """
    try:
        market_data = client.marketdata_history_by_conid(
            conid, period="1d", bar="1d", outside_rth=True
        ).data

        if not market_data or "data" not in market_data or not market_data["data"]:
            raise MarketDataError(f"Could not get current market price for {symbol}")

        # Use the latest data point for the current price
        latest_data = market_data["data"][-1]
        current_price = float(latest_data.get("c", 0))  # 'c' is close price

        if current_price <= 0:
            raise MarketDataError(f"Invalid current price for {symbol}: {current_price}")

        logger.info(f"Retrieved current price for {symbol}: ${current_price}")
        return current_price

    except Exception as e:
        if isinstance(e, MarketDataError):
            raise
        raise MarketDataError(f"Error getting market data for {symbol}: {str(e)}")


def calculate_limit_price(current_price: float, side: str, percentage: float) -> float:
    """
    Calculate limit price based on current market price and percentage offset.

    Args:
        current_price: Current market price
        side: 'BUY' or 'SELL'
        percentage: Percentage offset from market price

    Returns:
        float: Calculated limit price
    """
    if side == "SELL":
        # For sell orders, add percentage above market
        price_multiplier = 1 + (percentage / 100)
    else:  # BUY
        # For buy orders, subtract percentage below market
        price_multiplier = 1 - (percentage / 100)

    limit_price = round(current_price * price_multiplier, 2)
    logger.info(
        f"Calculated limit price: ${limit_price} ({side} {percentage}% from ${current_price})"
    )
    return limit_price


def fetch_all_positions(client: IbkrClient) -> List[Dict[str, Any]]:
    """
    Fetch all positions using pagination.

    Args:
        client: Authenticated IBKR client

    Returns:
        List of position dictionaries
    """
    all_positions = []
    page = 0

    logger.info("Fetching positions with pagination")

    while True:
        try:
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
                time.sleep(0.5)  # Rate limiting
            else:
                # No more data or unexpected format
                break

        except Exception as page_error:
            logger.error(f"Error fetching positions page {page}: {page_error}")
            break

    logger.info(f"Retrieved total of {len(all_positions)} positions across {page + 1} pages")
    return all_positions


def find_position_by_symbol(
    positions: List[Dict[str, Any]], symbol: str, conid: str
) -> Dict[str, Any]:
    """
    Find a position by symbol or contract ID.

    Args:
        positions: List of position dictionaries
        symbol: Stock symbol to search for
        conid: Contract ID to search for

    Returns:
        Position dictionary

    Raises:
        PositionNotFoundError: If position is not found
    """
    # First try to match by conid
    for position in positions:
        if str(position.get("conid")) == conid:
            logger.info(f"Found position match by conid: {conid}")
            return position

    # If no match by conid, try to match by ticker (case insensitive)
    logger.info(f"No match by conid, trying to match by ticker: {symbol}")
    for position in positions:
        position_ticker = position.get("ticker", "")
        if position_ticker and position_ticker.upper() == symbol.upper():
            logger.info(f"Found position match by ticker: {position_ticker}")
            return position

    raise PositionNotFoundError(f"No position found for {symbol}")


def calculate_sell_quantity(
    position: Dict[str, Any], percentage_of_position: float, symbol: str
) -> int:
    """
    Calculate quantity to sell based on percentage of current position.

    Args:
        position: Position dictionary
        percentage_of_position: Percentage of position to sell
        symbol: Symbol for error messages

    Returns:
        int: Quantity to sell

    Raises:
        ValueError: If position is zero or invalid
    """
    current_position = float(position.get("position", 0))

    if current_position == 0:
        raise ValueError(f"Current position for {symbol} is zero")

    # Calculate quantity from percentage (round up to nearest integer)
    quantity_float = abs(current_position) * (percentage_of_position / 100)
    quantity = max(1, int(quantity_float + 0.99))  # Round up to nearest integer

    logger.info(
        f"Calculated sell quantity {quantity} from {percentage_of_position}% of position {current_position}"
    )
    return quantity


def calculate_buy_quantity(dollar_amount: float, limit_price: float) -> int:
    """
    Calculate quantity to buy based on dollar amount and limit price.

    Args:
        dollar_amount: Amount in USD to spend
        limit_price: Limit price per share

    Returns:
        int: Quantity to buy

    Raises:
        ValueError: If dollar amount is invalid
    """
    if dollar_amount <= 0:
        raise ValueError("Dollar amount must be greater than 0 for BUY orders")

    # Calculate quantity based on dollar amount and limit price (round up)
    quantity_float = dollar_amount / limit_price
    quantity = max(1, int(quantity_float + 0.99))  # Round up to nearest integer

    logger.info(f"Calculated buy quantity {quantity} from ${dollar_amount} at ${limit_price}")
    return quantity


def place_percentage_order(
    client: IbkrClient,
    symbol: str,
    conid: str,
    side: str,
    quantity: int,
    limit_price: float,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Place a percentage-based limit order.

    Args:
        client: Authenticated IBKR client
        symbol: Stock symbol
        conid: Contract ID
        side: 'BUY' or 'SELL'
        quantity: Number of shares
        limit_price: Limit price
        time_in_force: Time in force (default: GTC)

    Returns:
        Dict containing order result

    Raises:
        Exception: If order placement fails
    """
    # Generate a unique order tag
    order_tag = f'percentage-{symbol}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

    # Create the order request
    order_request = make_order_request(
        conid=conid,
        side=side,
        quantity=quantity,
        order_type="LMT",
        price=limit_price,
        acct_id=client.account_id,
        coid=order_tag,
        tif=time_in_force,
    )

    logger.info(f"Placing order: {order_request}")

    # Define answers for common questions
    answers = {
        QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
        QuestionType.ORDER_VALUE_LIMIT: True,
        QuestionType.MISSING_MARKET_DATA: True,
        QuestionType.STOP_ORDER_RISKS: True,
        "Unforeseen new question": True,
        "<h4>Confirm Mandatory Cap Price</h4>To avoid trading at a price that is not consistent with a fair and orderly market, IB may set a cap (for a buy order) or floor (for a sell order). THIS MAY CAUSE AN ORDER THAT WOULD OTHERWISE BE MARKETABLE NOT TO BE TRADED.": True,
    }

    # Place the order
    result = client.place_order(order_request, answers)

    if result.data:
        return {
            "status": "success",
            "message": f"Order placed successfully for {quantity} shares of {symbol} at ${limit_price}",
            "data": result.data,
            "order_tag": order_tag,
        }
    else:
        raise Exception(f"Error placing order: {result.error_message}")


def validate_percentage_order_request(data: Dict[str, Any], side: str) -> None:
    """
    Validate percentage order request data.

    Args:
        data: Request data dictionary
        side: Order side ('BUY' or 'SELL')

    Raises:
        ValueError: If validation fails
    """
    if side not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

    if side == "SELL":
        if "percentage_of_position" not in data:
            raise ValueError("percentage_of_position is required for SELL orders")

        percentage_of_position = float(data.get("percentage_of_position", 0))
        if percentage_of_position <= 0 or percentage_of_position > 100:
            raise ValueError("percentage_of_position must be between 0 and 100")

    elif side == "BUY":
        if "dollar_amount" not in data:
            raise ValueError("dollar_amount is required for BUY orders")

        dollar_amount = float(data.get("dollar_amount", 0))
        if dollar_amount <= 0:
            raise ValueError("dollar_amount must be greater than 0")


def cleanup_client_connection(client: Optional[IbkrClient]) -> None:
    """
    Safely cleanup IBKR client connection.

    Args:
        client: IBKR client to cleanup (can be None)
    """
    if client:
        try:
            client.logout()
            logger.info("Successfully logged out IBKR client")
        except Exception as e:
            logger.error(f"Error logging out IBKR client: {e}")
