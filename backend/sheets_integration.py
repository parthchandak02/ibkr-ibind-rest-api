"""
Google Sheets Integration Module

Simple interface for reading/writing trading data to Google Sheets.
Perfect for portfolio tracking, trade logging, and data sharing.
"""

import logging
import os
from datetime import datetime
from typing import Any, List, Optional

import gspread
from google.oauth2.service_account import Credentials

from .config import Config

logger = logging.getLogger(__name__)


class SheetsIntegration:
    """Google Sheets integration for IBKR trading data."""

    def __init__(self, credentials_dict: dict):
        """Initialize Google Sheets client."""
        self.credentials_dict = credentials_dict
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.client = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            if not self.credentials_dict:
                raise ValueError("Google Sheets credentials not found in config.json")
                
            # Use credentials from config.json
            credentials = Credentials.from_service_account_info(
                self.credentials_dict, scopes=self.scopes
            )
            logger.info("Using Google Sheets credentials from config.json")

            self.client = gspread.authorize(credentials)
            logger.info("Successfully authenticated with Google Sheets API")

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def open_spreadsheet_by_url(self, url: str):
        """Open spreadsheet by URL."""
        try:
            return self.client.open_by_url(url)
        except Exception as e:
            logger.error(f"Failed to open spreadsheet: {e}")
            raise

    def get_worksheet(self, spreadsheet, worksheet_name: str = None, index: int = 0):
        """Get worksheet by name or index."""
        try:
            if worksheet_name:
                return spreadsheet.worksheet(worksheet_name)
            else:
                return spreadsheet.get_worksheet(index)
        except Exception as e:
            logger.error(f"Failed to get worksheet: {e}")
            raise

    def read_all_records(self, worksheet) -> List[dict[str, Any]]:
        """Read all records from worksheet as list of dictionaries."""
        try:
            # Handle duplicate header issue by specifying expected headers
            expected_headers = ['Status', 'Stock Symbol', 'Price', 'Amount', 'Qty to buy', 'Frequency', 'Log']
            return worksheet.get_all_records(expected_headers=expected_headers)
        except Exception as e:
            logger.error(f"Failed to read records: {e}")
            # Fallback to default method if expected_headers fails
            try:
                return worksheet.get_all_records()
            except Exception as fallback_error:
                logger.error(f"Fallback read also failed: {fallback_error}")
                raise

    def append_row(self, worksheet, row_data: List[Any]):
        """Append a new row to the worksheet."""
        try:
            worksheet.append_row(row_data)
            logger.info(f"Successfully appended row: {row_data}")
        except Exception as e:
            logger.error(f"Failed to append row: {e}")
            raise

    def update_cell(self, worksheet, row: int, col: int, value: Any):
        """Update a specific cell."""
        try:
            worksheet.update_cell(row, col, value)
            logger.info(f"Updated cell ({row}, {col}) = {value}")
        except Exception as e:
            logger.error(f"Failed to update cell: {e}")
            raise

    def batch_update(self, worksheet, updates: List[dict]):
        """Perform batch updates for efficiency."""
        try:
            worksheet.batch_update(updates)
            logger.info(f"Successfully performed {len(updates)} batch updates")
        except Exception as e:
            logger.error(f"Failed to perform batch updates: {e}")
            raise

    def log_trade(
        self,
        spreadsheet_url: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = "MKT",
        worksheet_name: str = "Trades",
    ):
        """
        Log a trade to Google Sheets.

        Args:
            spreadsheet_url: URL of the Google Sheet
            symbol: Stock symbol
            side: BUY or SELL
            quantity: Number of shares
            price: Price per share
            order_type: Order type (MKT, LMT, etc.)
            worksheet_name: Name of worksheet to log to
        """
        try:
            spreadsheet = self.open_spreadsheet_by_url(spreadsheet_url)
            worksheet = self.get_worksheet(spreadsheet, worksheet_name)

            # Prepare trade data
            trade_data = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Timestamp
                symbol,
                side,
                quantity,
                price,
                quantity * price,  # Total value
                order_type,
                "Automated",  # Source
            ]

            self.append_row(worksheet, trade_data)
            logger.info(f"Logged trade: {symbol} {side} {quantity} @ ${price}")

        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
            raise

    def update_portfolio_snapshot(
        self,
        spreadsheet_url: str,
        positions_data: List[dict],
        worksheet_name: str = "Portfolio",
    ):
        """
        Update portfolio snapshot in Google Sheets.

        Args:
            spreadsheet_url: URL of the Google Sheet
            positions_data: List of position dictionaries from IBKR
            worksheet_name: Name of worksheet to update
        """
        try:
            spreadsheet = self.open_spreadsheet_by_url(spreadsheet_url)
            worksheet = self.get_worksheet(spreadsheet, worksheet_name)

            # Clear existing data (keep headers)
            worksheet.clear()

            # Add headers from config
            portfolio_headers = google_sheets_config.get('column_headers', {}).get('portfolio', {})
            headers = [
                portfolio_headers.get('symbol', 'Symbol'),
                portfolio_headers.get('position', 'Position'),
                portfolio_headers.get('market_price', 'Market Price'),
                portfolio_headers.get('market_value', 'Market Value'),
                portfolio_headers.get('avg_cost', 'Avg Cost'),
                portfolio_headers.get('pnl', 'P&L'),
                portfolio_headers.get('pnl_percent', 'P&L %'),
                portfolio_headers.get('last_updated', 'Last Updated'),
            ]
            worksheet.append_row(headers)

            # Add position data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for position in positions_data:
                row_data = [
                    position.get("ticker", ""),
                    position.get("position", 0),
                    position.get("mktPrice", 0),
                    position.get("mktValue", 0),
                    position.get("avgPrice", 0),
                    position.get("unrealizedPL", 0),
                    position.get("unrealizedPLPercent", 0),
                    timestamp,
                ]
                worksheet.append_row(row_data)

            logger.info(
                f"Updated portfolio snapshot with {len(positions_data)} positions"
            )

        except Exception as e:
            logger.error(f"Failed to update portfolio snapshot: {e}")
            raise


# Convenience function for quick setup
def get_sheets_client() -> SheetsIntegration:
    """Get authenticated Google Sheets client."""
    config = Config()
    google_sheets_config = config.get_google_sheets_config()
    credentials_dict = google_sheets_config.get("credentials")
    
    return SheetsIntegration(
        credentials_dict=credentials_dict
    )


# Example usage functions
def example_read_sheet():
    """Example: Read data from Google Sheets."""
    sheets = get_sheets_client()
    config = Config()
    google_sheets_config = config.get_google_sheets_config()
    url = google_sheets_config.get("spreadsheet_url")

    try:
        spreadsheet = sheets.open_spreadsheet_by_url(url)
        worksheet = sheets.get_worksheet(spreadsheet, index=0)

        # Read all data
        data = sheets.read_all_records(worksheet)
        print(f"Found {len(data)} records")

        return data
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return None


def example_write_trade():
    """Example: Log a trade to Google Sheets."""
    sheets = get_sheets_client()
    config = Config()
    google_sheets_config = config.get_google_sheets_config()
    url = google_sheets_config.get("spreadsheet_url")
    example_data = google_sheets_config.get("example_data", {})

    try:
        sheets.log_trade(
            spreadsheet_url=url,
            symbol=example_data.get("symbol", "AAPL"),
            side=example_data.get("side", "BUY"),
            quantity=example_data.get("quantity", 10),
            price=example_data.get("price", 150.00),
            order_type=example_data.get("order_type", "LMT"),
        )
        print("Trade logged successfully!")
    except Exception as e:
        print(f"Error logging trade: {e}")


if __name__ == "__main__":
    # Test the integration
    print("Testing Google Sheets integration...")

    # Test reading
    data = example_read_sheet()
    if data:
        print("✅ Reading works!")

    # Test writing (uncomment when ready)
    # example_write_trade()
