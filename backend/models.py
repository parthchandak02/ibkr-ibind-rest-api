#!/usr/bin/env python3
"""
Data Models for IBKR Trading System

This module defines data classes and models used throughout the application.
Following proper OOP principles and type safety.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderFrequency(Enum):
    """Order frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP_LMT"


@dataclass
class ColumnHeaders:
    """Column headers configuration for Google Sheets."""
    status: str
    stock_symbol: str
    price: str
    amount: str
    qty_to_buy: str
    frequency: str
    log: str
    
    @classmethod
    def from_config(cls, config: Dict[str, str]) -> 'ColumnHeaders':
        """Create ColumnHeaders from configuration dictionary."""
        return cls(
            status=config.get('status', 'Status'),
            stock_symbol=config.get('stock_symbol', 'Stock Symbol'),
            price=config.get('price', 'Price'),
            amount=config.get('amount', 'Amount'),
            qty_to_buy=config.get('qty_to_buy', 'Qty to buy'),
            frequency=config.get('frequency', 'Frequency'),
            log=config.get('log', 'Log')
        )


@dataclass
class RecurringOrder:
    """Represents a recurring order from Google Sheets."""
    status: OrderStatus
    stock_symbol: str
    price: Optional[float]
    amount: Optional[float]  # Reference price/amount info
    qty_to_buy: int  # Primary field - quantity of shares to buy
    frequency: OrderFrequency
    log: Optional[str] = None
    
    @classmethod
    def from_sheet_row(cls, row: Dict[str, Union[str, float, int]], headers: ColumnHeaders) -> 'RecurringOrder':
        """Create RecurringOrder from Google Sheets row data."""
        try:
            # Parse status
            status_str = str(row.get(headers.status, '')).lower().strip()
            status = OrderStatus.ACTIVE if status_str == 'active' else OrderStatus.INACTIVE
            
            # Parse frequency
            freq_str = str(row.get(headers.frequency, '')).lower().strip()
            frequency_map = {
                'daily': OrderFrequency.DAILY,
                'weekly': OrderFrequency.WEEKLY,
                'monthly': OrderFrequency.MONTHLY
            }
            frequency = frequency_map.get(freq_str, OrderFrequency.WEEKLY)
            
            # Parse numeric values
            price = None
            if row.get(headers.price):
                try:
                    price = float(row[headers.price])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price value: {row.get(headers.price)}")
            
            amount = None
            if row.get(headers.amount):
                try:
                    amount = float(row[headers.amount])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount value: {row.get(headers.amount)}")
            
            # qty_to_buy is now the primary field (required)
            qty_to_buy = 0
            if row.get(headers.qty_to_buy):
                try:
                    qty_to_buy = int(row[headers.qty_to_buy])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid qty_to_buy value: {row.get(headers.qty_to_buy)}")
                    raise ValueError(f"Invalid quantity: {row.get(headers.qty_to_buy)}")
            
            if qty_to_buy <= 0:
                raise ValueError(f"Quantity must be greater than 0, got: {qty_to_buy}")
            
            return cls(
                status=status,
                stock_symbol=str(row.get(headers.stock_symbol, '')).upper().strip(),
                price=price,
                amount=amount,
                qty_to_buy=qty_to_buy,
                frequency=frequency,
                log=str(row.get(headers.log, '') or '')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse sheet row: {e}")
            raise ValueError(f"Invalid sheet row data: {e}") from e
    
    def is_valid_for_execution(self) -> bool:
        """Check if this order is valid for execution."""
        return (
            self.status == OrderStatus.ACTIVE and
            bool(self.stock_symbol) and
            self.qty_to_buy > 0
        )


@dataclass
class ExecutionDetails:
    """Details of order execution."""
    symbol: str
    target_quantity: int  # Number of shares to buy
    timestamp: datetime
    frequency: OrderFrequency
    market_price: Optional[float] = None
    estimated_cost: Optional[float] = None  # quantity * market_price
    order_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Union[str, float, int, None]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "target_quantity": self.target_quantity,
            "timestamp": self.timestamp.isoformat(),
            "frequency": self.frequency.value,
            "market_price": self.market_price,
            "estimated_cost": self.estimated_cost,
            "order_id": self.order_id,
            "status": self.status,
            "error": self.error
        }


@dataclass
class SchedulingConfig:
    """Scheduling configuration."""
    timezone: str
    daily_check_time: Dict[str, int]
    schedule_types: Dict[str, Dict[str, int]]
    market_hours: Dict[str, int]
    grace_time_minutes: int
    
    @classmethod
    def from_config(cls, config: Dict) -> 'SchedulingConfig':
        """Create SchedulingConfig from configuration dictionary."""
        return cls(
            timezone=config.get('timezone', 'US/Eastern'),
            daily_check_time=config.get('daily_check_time', {'hour': 9, 'minute': 0}),
            schedule_types=config.get('schedule_types', {}),
            market_hours=config.get('market_hours', {}),
            grace_time_minutes=config.get('grace_time_minutes', 5)
        )
