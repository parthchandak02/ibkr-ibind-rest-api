"""
Data export module for the IBKR REST API.

This module handles data export functionality including CSV generation
and position data formatting.
"""

import csv
import datetime
import io
import logging
import time
from typing import List, Dict, Any

from flask import Response

from .utils import get_ibkr_client
from .account_operations import fetch_all_positions_paginated

logger = logging.getLogger(__name__)


# Position fetching function moved to account_operations.py to avoid duplication
# Now importing fetch_all_positions_paginated from account_operations module


def format_position_for_csv(position: Dict[str, Any]) -> Dict[str, str]:
    """
    Format a single position for CSV export.
    
    Args:
        position: Position dictionary from IBKR API
        
    Returns:
        Formatted dictionary for CSV writing
    """
    # Extract numerical values safely
    position_qty = float(position.get("position", 0) or 0)
    avg_cost = float(position.get("avgPrice", 0) or 0)
    market_price = float(position.get("mktPrice", 0) or 0)
    market_value = float(position.get("mktValue", 0) or 0)
    unrealized_pnl = float(position.get("unrealizedPnl", 0) or 0)

    # Calculate P&L percentage if we have valid prices
    if avg_cost > 0 and market_price > 0:
        pnl_percent = ((market_price - avg_cost) / avg_cost) * 100
    else:
        pnl_percent = 0

    # Calculate cost basis
    cost_basis = position_qty * avg_cost

    # Get symbol - try different fields that might contain it
    symbol = (
        position.get("ticker", "")
        or position.get("contractDesc", "")
        or position.get("symbol", "")
    )

    # Format row with readable column names
    return {
        "Symbol": symbol,
        "Name": position.get("name", ""),
        "Position": f"{position_qty:,.2f}",
        "Avg Cost": f"${avg_cost:,.2f}",
        "Market Price": f"${market_price:,.2f}",
        "Market Value": f"${market_value:,.2f}",
        "Cost Basis": f"${cost_basis:,.2f}",
        "Unrealized P&L": f"${unrealized_pnl:,.2f}",
        "P&L %": f"{pnl_percent:.2f}%",
        "Currency": position.get("currency", ""),
        "Sector": position.get("sector", ""),
        "Type": position.get("type", ""),
        "Country": position.get("countryCode", ""),
        "Exchange": position.get("listingExchange", ""),
    }


def generate_positions_csv() -> Response:
    """
    Generate a CSV file of all positions.
    
    Returns:
        Flask Response with CSV data
    """
    # Fetch all positions
    all_positions = fetch_all_positions_paginated()

    # Create CSV data
    output = io.StringIO()
    fieldnames = [
        "Symbol",
        "Name",
        "Position",
        "Avg Cost",
        "Market Price",
        "Market Value",
        "Cost Basis",
        "Unrealized P&L",
        "P&L %",
        "Currency",
        "Sector",
        "Type",
        "Country",
        "Exchange",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    # Write positions to CSV with enhanced formatting
    for position in all_positions:
        formatted_row = format_position_for_csv(position)
        writer.writerow(formatted_row)

    # Prepare the response
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=positions_{timestamp}.csv",
            "Content-Type": "text/csv",
        },
    )
    return response


def get_positions_with_limit(limit: int = 10) -> Dict[str, Any]:
    """
    Get positions with optional limit.
    
    Args:
        limit: Maximum number of positions to return
        
    Returns:
        Dictionary with positions and summary information
    """
    # Fetch positions with pagination
    all_positions = []
    page = 0

    while True:
        try:
            client = get_ibkr_client()
            if not client:
                raise Exception("IBKR client not available")
                
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
            logger.error(f"Error on page {page}: {page_error}")
            break

    # Return only the requested number of positions
    positions_to_return = all_positions[:limit]

    # Add summary information
    position_summary = {
        "total_available": len(all_positions),
        "displayed": len(positions_to_return),
        "timestamp": datetime.datetime.now().isoformat(),
    }

    return {
        "summary": position_summary,
        "positions": positions_to_return,
    } 