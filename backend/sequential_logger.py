#!/usr/bin/env python3
"""
Sequential Google Sheets Logger

Based on research from Stack Overflow and best practices for finding
the next empty column in a specific row for sequential logging.
"""

import logging
from datetime import datetime
from typing import Optional

from gspread.utils import rowcol_to_a1

from .config import Config
from .exceptions import SheetsIntegrationError
from .models import ExecutionDetails, RecurringOrder
from .sheets_integration import get_sheets_client

logger = logging.getLogger(__name__)


class SequentialLogger:
    """Handles sequential logging to Google Sheets columns."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the sequential logger."""
        self.config = config or Config()
        self.google_config = self.config.get_google_sheets_config()
        self.sheet_url = self.google_config.get("spreadsheet_url")
        self.column_headers = self.google_config.get('column_headers', {}).get('recurring_orders', {})
        self.sheets_client = get_sheets_client()
    
    def log_execution(self, order: RecurringOrder, execution_details: ExecutionDetails) -> str:
        """
        Log execution to the next empty column in the order's row.
        
        Based on research: Use worksheet.row_values(row) to find next empty column.
        
        Args:
            order: The order that was executed
            execution_details: Details of the execution
            
        Returns:
            The log message that was written
            
        Raises:
            SheetsIntegrationError: If logging fails
        """
        try:
            # Open the spreadsheet
            spreadsheet = self.sheets_client.open_spreadsheet_by_url(self.sheet_url)
            worksheet = self.sheets_client.get_worksheet(spreadsheet, 0)
            
            # Find the row for this stock symbol (handle duplicate headers)
            try:
                expected_headers = ['Status', 'Stock Symbol', 'Price', 'Amount', 'Qty to buy', 'Frequency', 'Log']
                all_records = worksheet.get_all_records(expected_headers=expected_headers)
            except:
                # Fallback to default method
                all_records = worksheet.get_all_records()
            
            target_row = None
            
            for i, record in enumerate(all_records, start=2):  # Start at row 2 (header is row 1)
                if record.get(self.column_headers.get('stock_symbol', 'Stock Symbol')) == order.stock_symbol:
                    target_row = i
                    break
            
            if not target_row:
                raise SheetsIntegrationError(f"Could not find row for stock symbol: {order.stock_symbol}")
            
            # Create log message
            log_message = self._create_log_message(order, execution_details)
            
            # Find next empty column using research-based method
            row_values = worksheet.row_values(target_row)
            next_col = len(row_values) + 1
            
            # Ensure we start from at least column G (7)
            if next_col < 7:
                next_col = 7
            
            # Update the cell
            worksheet.update_cell(target_row, next_col, log_message)
            
            # Log success with cell address
            cell_address = rowcol_to_a1(target_row, next_col)
            logger.info(f"✅ Logged execution for {order.stock_symbol} in cell {cell_address}")
            
            return log_message
            
        except Exception as e:
            error_msg = f"Failed to log execution for {order.stock_symbol}: {e}"
            logger.error(error_msg)
            raise SheetsIntegrationError(error_msg) from e
    
    def _create_log_message(self, order: RecurringOrder, execution_details: ExecutionDetails) -> str:
        """Create a formatted log message for the execution."""
        timestamp = execution_details.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if execution_details.status == "success":
            # Success: "✅ 2025-09-18 00:03:57: 1 shares @ $1.90 | ID: 1257530032"
            price_info = f" @ ${execution_details.market_price:.2f}" if execution_details.market_price else ""
            cost_info = f" (${execution_details.estimated_cost:.2f})" if execution_details.estimated_cost else ""
            order_id_info = f" | ID: {execution_details.order_id}" if execution_details.order_id else ""
            
            return f"✅ {timestamp}: {order.qty_to_buy} shares{price_info}{cost_info}{order_id_info}"
        else:
            # Failure: "❌ 2025-09-18 00:03:57: FAILED - Error message"
            error_info = f" - {execution_details.error}" if execution_details.error else ""
            return f"❌ {timestamp}: FAILED{error_info}"


def log_order_execution(order: RecurringOrder, execution_details: ExecutionDetails) -> str:
    """
    Convenience function to log an order execution.
    
    Args:
        order: The order that was executed
        execution_details: Details of the execution
        
    Returns:
        The log message that was written
    """
    logger = SequentialLogger()
    return logger.log_execution(order, execution_details)
