#!/usr/bin/env python3
"""
Custom Exceptions for IBKR Trading System

This module defines custom exception classes for better error handling
and debugging throughout the application.
"""

from typing import Optional


class IBKRTradingError(Exception):
    """Base exception for IBKR trading system errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(IBKRTradingError):
    """Raised when there are configuration-related errors."""
    pass


class SheetsIntegrationError(IBKRTradingError):
    """Raised when Google Sheets operations fail."""
    pass


class OrderExecutionError(IBKRTradingError):
    """Raised when order execution fails."""
    pass


class ValidationError(IBKRTradingError):
    """Raised when data validation fails."""
    pass


class APIConnectionError(IBKRTradingError):
    """Raised when API connection fails."""
    pass


class SchedulingError(IBKRTradingError):
    """Raised when scheduling operations fail."""
    pass


class SymbolResolutionError(IBKRTradingError):
    """Raised when symbol resolution fails."""
    pass


class NotificationError(IBKRTradingError):
    """Raised when notification sending fails."""
    pass


# Legacy exception for backward compatibility
RecurringOrdersError = IBKRTradingError
