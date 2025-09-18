#!/usr/bin/env python3
"""
Input Validation Module for IBKR Trading System

This module provides comprehensive input validation functions
following best practices for data validation and type checking.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging

from .exceptions import ValidationError
from .models import OrderFrequency, OrderStatus, OrderType, OrderSide

logger = logging.getLogger(__name__)


class Validators:
    """Collection of validation methods for various data types."""
    
    @staticmethod
    def validate_stock_symbol(symbol: Any) -> str:
        """
        Validate and normalize stock symbol.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            Normalized stock symbol (uppercase, stripped)
            
        Raises:
            ValidationError: If symbol is invalid
        """
        if not symbol:
            raise ValidationError("Stock symbol cannot be empty")
        
        symbol_str = str(symbol).strip().upper()
        
        # Basic symbol validation (letters and optionally numbers)
        if not re.match(r'^[A-Z]{1,5}[0-9]*$', symbol_str):
            raise ValidationError(f"Invalid stock symbol format: {symbol}")
        
        return symbol_str
    
    @staticmethod
    def validate_amount(amount: Any, min_amount: float = 0.01) -> float:
        """
        Validate monetary amount.
        
        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            
        Returns:
            Validated amount as float
            
        Raises:
            ValidationError: If amount is invalid
        """
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid amount format: {amount}")
        
        if amount_float < min_amount:
            raise ValidationError(f"Amount must be at least ${min_amount}")
        
        if amount_float > 1_000_000:  # Reasonable upper limit
            raise ValidationError(f"Amount too large: ${amount_float}")
        
        return round(amount_float, 2)
    
    @staticmethod
    def validate_quantity(quantity: Any, min_quantity: int = 1) -> int:
        """
        Validate share quantity.
        
        Args:
            quantity: Quantity to validate
            min_quantity: Minimum allowed quantity
            
        Returns:
            Validated quantity as integer
            
        Raises:
            ValidationError: If quantity is invalid
        """
        try:
            quantity_int = int(quantity)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid quantity format: {quantity}")
        
        if quantity_int < min_quantity:
            raise ValidationError(f"Quantity must be at least {min_quantity}")
        
        if quantity_int > 1_000_000:  # Reasonable upper limit
            raise ValidationError(f"Quantity too large: {quantity_int}")
        
        return quantity_int
    
    @staticmethod
    def validate_frequency(frequency: Any) -> OrderFrequency:
        """
        Validate order frequency.
        
        Args:
            frequency: Frequency to validate
            
        Returns:
            Validated OrderFrequency enum
            
        Raises:
            ValidationError: If frequency is invalid
        """
        if not frequency:
            raise ValidationError("Frequency cannot be empty")
        
        freq_str = str(frequency).lower().strip()
        
        frequency_map = {
            'daily': OrderFrequency.DAILY,
            'weekly': OrderFrequency.WEEKLY,
            'monthly': OrderFrequency.MONTHLY
        }
        
        if freq_str not in frequency_map:
            valid_frequencies = list(frequency_map.keys())
            raise ValidationError(f"Invalid frequency: {frequency}. Must be one of: {valid_frequencies}")
        
        return frequency_map[freq_str]
    
    @staticmethod
    def validate_order_status(status: Any) -> OrderStatus:
        """
        Validate order status.
        
        Args:
            status: Status to validate
            
        Returns:
            Validated OrderStatus enum
            
        Raises:
            ValidationError: If status is invalid
        """
        if not status:
            raise ValidationError("Status cannot be empty")
        
        status_str = str(status).lower().strip()
        
        status_map = {
            'active': OrderStatus.ACTIVE,
            'inactive': OrderStatus.INACTIVE,
            'pending': OrderStatus.PENDING,
            'completed': OrderStatus.COMPLETED,
            'failed': OrderStatus.FAILED
        }
        
        if status_str not in status_map:
            valid_statuses = list(status_map.keys())
            raise ValidationError(f"Invalid status: {status}. Must be one of: {valid_statuses}")
        
        return status_map[status_str]
    
    @staticmethod
    def validate_url(url: Any, schemes: Optional[List[str]] = None) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            schemes: Allowed URL schemes (default: ['http', 'https'])
            
        Returns:
            Validated URL string
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError("URL cannot be empty")
        
        if schemes is None:
            schemes = ['http', 'https']
        
        url_str = str(url).strip()
        
        try:
            parsed = urlparse(url_str)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(f"Invalid URL format: {url}")
            
            if parsed.scheme not in schemes:
                raise ValidationError(f"Invalid URL scheme: {parsed.scheme}. Must be one of: {schemes}")
            
        except Exception as e:
            raise ValidationError(f"Invalid URL: {url}") from e
        
        return url_str
    
    @staticmethod
    def validate_config_dict(config: Any, required_keys: Optional[List[str]] = None) -> Dict:
        """
        Validate configuration dictionary.
        
        Args:
            config: Configuration to validate
            required_keys: List of required keys
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise ValidationError(f"Missing required configuration keys: {missing_keys}")
        
        return config
    
    @staticmethod
    def validate_sheet_row(row: Dict[str, Any], required_columns: List[str]) -> Dict[str, Any]:
        """
        Validate Google Sheets row data.
        
        Args:
            row: Row data from Google Sheets
            required_columns: List of required column names
            
        Returns:
            Validated row data
            
        Raises:
            ValidationError: If row data is invalid
        """
        if not isinstance(row, dict):
            raise ValidationError("Sheet row must be a dictionary")
        
        missing_columns = [col for col in required_columns if col not in row or not row[col]]
        if missing_columns:
            raise ValidationError(f"Missing required columns in sheet row: {missing_columns}")
        
        return row


def validate_order_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate order request data.
    
    Args:
        data: Order request data
        
    Returns:
        Validated and normalized order data
        
    Raises:
        ValidationError: If order data is invalid
    """
    validators = Validators()
    
    # Required fields
    required_fields = ['symbol', 'side', 'order_type']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    # Validate and normalize
    validated_data = {
        'symbol': validators.validate_stock_symbol(data['symbol']),
        'side': data['side'].upper() if data['side'] else '',
        'order_type': data['order_type'].upper() if data['order_type'] else ''
    }
    
    # Validate side
    if validated_data['side'] not in [side.value for side in OrderSide]:
        valid_sides = [side.value for side in OrderSide]
        raise ValidationError(f"Invalid side: {data['side']}. Must be one of: {valid_sides}")
    
    # Validate order type
    if validated_data['order_type'] not in [ot.value for ot in OrderType]:
        valid_types = [ot.value for ot in OrderType]
        raise ValidationError(f"Invalid order type: {data['order_type']}. Must be one of: {valid_types}")
    
    # Validate quantity or cash_qty
    if 'quantity' in data and data['quantity']:
        validated_data['quantity'] = validators.validate_quantity(data['quantity'])
    elif 'cash_qty' in data and data['cash_qty']:
        validated_data['cash_qty'] = validators.validate_amount(data['cash_qty'])
    else:
        raise ValidationError("Either 'quantity' or 'cash_qty' must be provided")
    
    # Optional fields
    if 'price' in data and data['price']:
        validated_data['price'] = validators.validate_amount(data['price'])
    
    if 'tif' in data:
        valid_tifs = ['DAY', 'GTC', 'IOC', 'FOK']
        if data['tif'] not in valid_tifs:
            raise ValidationError(f"Invalid time in force: {data['tif']}. Must be one of: {valid_tifs}")
        validated_data['tif'] = data['tif']
    
    return validated_data
