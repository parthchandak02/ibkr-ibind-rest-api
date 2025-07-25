"""
Market data module for the IBKR REST API.

This module handles market data retrieval and processing.
"""

import logging
from typing import Dict, List, Optional

from .utils import get_ibkr_client

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved."""
    pass


def get_market_data_for_conids(conids: List[str]) -> List[Dict]:
    """
    Get market data for a list of contract IDs.
    
    Args:
        conids: List of contract IDs as strings
        
    Returns:
        List of market data dictionaries
        
    Raises:
        MarketDataError: If market data cannot be retrieved
    """
    client = get_ibkr_client()
    if not client:
        raise MarketDataError("IBKR client not available")
    
    if not conids:
        raise MarketDataError("No contract IDs provided")
    
    try:
        # Process the first conid (this endpoint handles one at a time)
        conid = conids[0]
        
        # Get recent market data
        response = client.marketdata_history_by_conid(
            conid=conid,
            period='1d', 
            bar='1d', 
            outside_rth=True
        )
        
        market_data = response.data if hasattr(response, 'data') else response
        
        if market_data and 'data' in market_data and market_data['data']:
            # Get the latest data point
            latest_data = market_data['data'][-1]
            price = latest_data.get('c')  # 'c' is the close price
            
            if price:
                # Create response in expected format
                snapshot_data = [{
                    'conid': conid,
                    'last': price,
                    'close': price
                }]
                return snapshot_data
        
        raise MarketDataError(f"Could not retrieve price for conid {conid}")
        
    except Exception as e:
        logger.error(f"Failed to get market data for conids {conids}: {e}")
        if isinstance(e, MarketDataError):
            raise
        raise MarketDataError(f"Error retrieving market data: {str(e)}")


def get_current_price_for_symbol(symbol: str, conid: str) -> float:
    """
    Get current price for a symbol using its contract ID.
    
    Args:
        symbol: Stock symbol for logging
        conid: Contract ID
        
    Returns:
        Current price as float
        
    Raises:
        MarketDataError: If price cannot be retrieved
    """
    client = get_ibkr_client()
    if not client:
        raise MarketDataError("IBKR client not available")
    
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