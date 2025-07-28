"""
Account operations module for the IBKR REST API.

This module handles account data retrieval including account summary,
ledger information, and position aggregation.
"""

import datetime
import logging
import time
from typing import Dict, Any, List

from .utils import get_ibkr_client

logger = logging.getLogger(__name__)


def get_complete_account_data() -> Dict[str, Any]:
    """
    Get complete account data including positions, ledger, and account summary.
    
    Returns:
        Dictionary containing all account information
    """
    client = get_ibkr_client()
    if not client:
        raise Exception("IBKR client not available")

    # Ensure we have an account ID
    if not client.account_id:
        accounts = client.portfolio_accounts().data
        if accounts and len(accounts) > 0:
            client.account_id = accounts[0]["accountId"]
        else:
            raise Exception("No account ID available")

    # Initialize account data structure
    account_data = {}
    
    # Get basic account information
    account_data["accounts"] = client.portfolio_accounts().data
    account_data["selected_account"] = client.account_id

    # Get ledger information
    try:
        ledger = client.get_ledger().data
        account_data["ledger"] = ledger
    except Exception as e:
        logger.warning(f"Could not retrieve ledger data: {e}")
        account_data["ledger"] = {}

    # Fetch all positions using pagination
    all_positions = fetch_all_positions_paginated()
    
    account_data["positions"] = all_positions
    account_data["portfolio_summary"] = {
        "total_positions": len(all_positions),
        "timestamp": datetime.datetime.now().isoformat(),
    }

    return account_data


def fetch_all_positions_paginated() -> List[Dict[str, Any]]:
    """
    Fetch all positions using pagination with detailed logging.
        
    Returns:
        List of all positions
        
    Raises:
        Exception: If IBKR client is not available
    """
    client = get_ibkr_client()
    if not client:
        raise Exception("IBKR client not available")
        
    all_positions = []
    page = 0

    logger.info(f"Starting position pagination at page {page}")

    while True:
        try:
            logger.info(f"Attempting to fetch positions page: {page}")
            response = client.positions(page=page)
            current_page_positions = response.data

            logger.info(
                f"Response type: {type(response.data)}, "
                f"Count: {len(current_page_positions) if isinstance(current_page_positions, list) else 'not a list'}"
            )

            if isinstance(current_page_positions, list) and current_page_positions:
                logger.info(f"Page {page} has {len(current_page_positions)} positions")
                all_positions.extend(current_page_positions)
                logger.info(f"Total positions so far: {len(all_positions)}")

                # The API returns up to 100 items per page
                # If fewer items returned, we've reached the last page
                if len(current_page_positions) < 100:
                    logger.info(f"Last page detected - fewer than 100 positions on page {page}")
                    break

                # If we got exactly 100 positions, try the next page
                logger.info(f"Got exactly 100 positions on page {page}, checking next page")
                page += 1
                time.sleep(0.5)  # Delay between requests
            else:
                logger.info(f"No positions found on page {page} or unexpected data format")
                break
                
        except Exception as page_error:
            logger.error(f"Error on page {page}: {page_error}")
            break

    logger.info(f"Retrieved total of {len(all_positions)} positions across {page+1} pages")
    return all_positions


def get_live_orders() -> Dict[str, Any]:
    """
    Get all live orders for the account.
    
    Returns:
        Dictionary containing orders and snapshot information
    """
    client = get_ibkr_client()
    if not client:
        raise Exception("IBKR client not available")

    response = client.live_orders()

    # Check if we have a valid response with orders
    if response and hasattr(response, "data") and isinstance(response.data, dict):
        orders = response.data.get("orders", [])
        return {
            "orders": orders, 
            "snapshot": response.data.get("snapshot", False)
        }
    else:
        return {
            "orders": [], 
            "snapshot": False
        }


def get_order_details(order_id: str) -> Dict[str, Any]:
    """
    Get details for a specific order by its ID.
    
    Args:
        order_id: The order ID to retrieve
        
    Returns:
        Order details dictionary
    """
    client = get_ibkr_client()
    if not client:
        raise Exception("IBKR client not available")

    order_details = client.order_status(order_id).data
    return order_details 