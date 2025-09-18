#!/usr/bin/env python3
"""
Recurring Orders System for IBKR Trading API

This module provides automated recurring order execution based on Google Sheets data.
Supports Daily, Weekly, and Monthly scheduling with EST timezone handling.

Features:
- APScheduler for robust scheduling
- Discord webhook notifications  
- Google Sheets integration for order management
- API server integration for order execution (via HTTP requests)
- Comprehensive logging and error handling
"""

import logging
import os
import sys
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .config import Config
from .exceptions import (
    IBKRTradingError, 
    SheetsIntegrationError, 
    OrderExecutionError, 
    ConfigurationError,
    NotificationError,
    RecurringOrdersError  # Legacy compatibility
)
from .models import (
    ColumnHeaders, 
    RecurringOrder, 
    ExecutionDetails, 
    SchedulingConfig,
    OrderFrequency
)
from .sheets_integration import get_sheets_client
from .validators import Validators

logger = logging.getLogger(__name__)


class RecurringOrdersManager:
    """
    Manages automated recurring orders from Google Sheets.
    
    Handles scheduling, execution, logging, and notifications.
    Uses API server for order execution.
    
    This class follows proper OOP principles with dependency injection,
    comprehensive error handling, and type safety.
    """
    
    def __init__(
        self, 
        config: Optional[Config] = None,
        sheet_url: Optional[str] = None,
        discord_webhook: Optional[str] = None,
        api_base_url: Optional[str] = None
    ):
        """
        Initialize the recurring orders manager.
        
        Args:
            config: Configuration instance (injected dependency)
            sheet_url: Google Sheets URL override
            discord_webhook: Discord webhook URL override  
            api_base_url: API server base URL override
        """
        # Dependency injection - use provided config or create new one
        self.config = config or Config()
        
        # Load configurations
        self._load_configurations()
        
        # Override URLs if provided
        self.sheet_url = sheet_url or self._google_sheets_config.get("spreadsheet_url")
        self.discord_webhook = discord_webhook or self._discord_config.get("webhook_url")
        self.api_base_url = api_base_url or self.config.get_api_base_url()
        
        # Validate required configurations
        self._validate_configuration()
        
        # Initialize state
        self.scheduler: Optional[BackgroundScheduler] = None
        self.sheets_client = None
        
        # Initialize clients
        self._initialize_clients()
    
    def _load_configurations(self) -> None:
        """Load all required configurations."""
        try:
            self._google_sheets_config = self.config.get_google_sheets_config()
            self._discord_config = self.config.get_discord_config()
            self._settings = self.config.get_settings()
            self._scheduling_config = SchedulingConfig.from_config(
                self.config.get_scheduling_config()
            )
            self.column_headers = ColumnHeaders.from_config(
                self._google_sheets_config.get('column_headers', {}).get('recurring_orders', {})
            )
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configurations: {e}") from e
    
    def _validate_configuration(self) -> None:
        """Validate that all required configurations are present."""
        validators = Validators()
        
        if not self.sheet_url:
            raise ConfigurationError("Google Sheets URL not configured")
        
        if not self.discord_webhook:
            raise ConfigurationError("Discord webhook URL not configured")
        
        if not self.api_base_url:
            raise ConfigurationError("API server base URL not configured")
        
        # Validate URLs
        try:
            validators.validate_url(self.sheet_url, ['https'])
            validators.validate_url(self.discord_webhook, ['https'])
            validators.validate_url(self.api_base_url, ['http', 'https'])
        except Exception as e:
            raise ConfigurationError(f"Invalid URL configuration: {e}") from e
    
    def _initialize_clients(self):
        """Initialize Google Sheets client and verify API server connection."""
        try:
            self.sheets_client = get_sheets_client()
            
            # Test API server connection
            health_response = requests.get(f"{self.api_base_url}/health", timeout=10)
            health_response.raise_for_status()
            health_data = health_response.json()
            
            if not health_data.get("ibkr_connected"):
                raise RecurringOrdersError("API server reports IBKR not connected")
                    
            logger.info("Successfully initialized Google Sheets client and verified API server connection")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API server connection failed: {e}")
            raise RecurringOrdersError(f"Failed to connect to API server at {self.api_base_url}: {e}") from e
        except Exception as e:
            logger.error(f"Client initialization failed: {e}")
            raise RecurringOrdersError(f"Failed to initialize clients: {e}") from e
    
    def read_recurring_orders(self) -> List[Dict]:
        """
        Read recurring orders from Google Sheets.
        
        Returns:
            List of order dictionaries with Status, Stock Symbol, Amount, Frequency, Log
        """
        try:
            spreadsheet = self.sheets_client.open_spreadsheet_by_url(self.sheet_url)
            worksheet = self.sheets_client.get_worksheet(spreadsheet, "Recurring Orders - Python")
            
            raw_orders = self.sheets_client.read_all_records(worksheet)
            logger.info(f"Retrieved {len(raw_orders)} raw orders from sheet")
            
            # Parse orders using proper data models
            valid_orders = []
            for i, row in enumerate(raw_orders, start=2):  # Start at row 2 (header is row 1)
                try:
                    order = RecurringOrder.from_sheet_row(row, self.column_headers)
                    if order.is_valid_for_execution():
                        valid_orders.append(order)
                    else:
                        logger.debug(f"Skipping invalid/inactive order on row {i}: {order.stock_symbol}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse order on row {i}: {e}")
                    continue
            
            logger.info(f"Parsed {len(valid_orders)} valid active orders")
            return valid_orders
            
        except Exception as e:
            logger.error(f"Failed to read recurring orders: {e}")
            raise RecurringOrdersError(f"Failed to read orders: {e}") from e
    
    def should_execute_today(self, frequency: str) -> bool:
        """
        Check if orders with given frequency should execute today.
        
        Args:
            frequency: Daily, Weekly, or Monthly
            
        Returns:
            True if should execute today
        """
        now_est = datetime.now(EST)
        
        if frequency.lower() == 'daily':
            return True
        elif frequency.lower() == 'weekly':
            # Monday = 0, Sunday = 6
            return now_est.weekday() == 0  # Monday
        elif frequency.lower() == 'monthly':
            return now_est.day == 1  # First day of month
        else:
            logger.warning(f"Unknown frequency: {frequency}")
            return False
    
    def execute_order(self, order: Dict) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
        """
        Execute a single recurring order via API server.
        
        Args:
            order: RecurringOrder object to execute
            
        Returns:
            ExecutionDetails object with execution results
            
        Raises:
            OrderExecutionError: If order execution fails
            ValidationError: If order data is invalid
        """
        validators = Validators()
        
        # Validate order
        if not order.is_valid_for_execution():
            raise ValidationError(f"Order {order.stock_symbol} is not valid for execution")
        
        # Create execution details
        execution_details = ExecutionDetails(
            symbol=order.stock_symbol,
            target_quantity=order.qty_to_buy,
            timestamp=datetime.now(pytz.timezone(self._scheduling_config.timezone)),
            frequency=order.frequency
        )
        
        try:
            # Get current market price for informational purposes (not needed for order)
            try:
                price_url = f"{self.api_base_url}/market-data/current-price/{order.stock_symbol}"
                price_response = requests.get(price_url, timeout=10)
                
                if price_response.status_code == 200:
                    price_data = price_response.json()
                    current_price = price_data.get('price', 0)
                    execution_details.market_price = current_price
                    
                    # Calculate estimated cost (quantity * market_price)
                    if current_price > 0:
                        execution_details.estimated_cost = order.qty_to_buy * current_price
                else:
                    logger.warning(f"Could not get current price for {order.stock_symbol} from API")
                    
            except Exception as price_error:
                logger.warning(f"Could not get current price for {order.stock_symbol}: {price_error}")
            
            # Create order tag with timestamp
            order_tag = f'recurring-{order.stock_symbol}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
            # Place order via API server using exact quantity of shares
            order_payload = {
                "symbol": order.stock_symbol,
                "side": "BUY", 
                "quantity": order.qty_to_buy,
                "order_type": "MKT",
                "tif": "DAY"
            }
            
            order_url = f"{self.api_base_url}/order/symbol"
            order_response = requests.post(
                order_url, 
                json=order_payload, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if order_response.status_code == 200:
                response_data = order_response.json()
                # Store API response in execution details (success case)
                
                # Extract order ID from API response
                order_id = None
                if response_data.get("status") == "success":
                    # Try to extract order ID from the response data
                    order_data = response_data.get("data", {})
                    if isinstance(order_data, list) and len(order_data) > 0:
                        order_id = order_data[0].get('order_id') or order_data[0].get('orderId')
                    elif isinstance(order_data, dict):
                        order_id = order_data.get('order_id') or order_data.get('orderId')
                    
                    # If not found in data, try the message
                    if not order_id and "order_id" in str(response_data):
                        import re
                        order_id_match = re.search(r'order_id[\'"]?\s*:\s*[\'"]?(\w+)', str(response_data))
                        if order_id_match:
                            order_id = order_id_match.group(1)
                    
                    execution_details.order_id = order_id
                    
                    # Create detailed success message for cash quantity order
                    price_info = f" @ ${execution_details.market_price:.2f}" if execution_details.market_price else ""
                    
                    cost_info = f" (${execution_details.estimated_cost:.2f})" if execution_details.estimated_cost else ""
                    success_msg = f"✅ **{order.stock_symbol}**: {order.qty_to_buy} shares{price_info}{cost_info}"
                    if order_id:
                        success_msg += f" | Order ID: {order_id}"
                    
                    execution_details.status = "success"
                    
                    logger.info(f"Order placed successfully via API: {order_tag}")
                    
                    return execution_details
                else:
                    # API returned success status but with error status in data
                    error_msg = response_data.get("message", "Unknown API error")
                    raise Exception(f"API error: {error_msg}")
            else:
                # HTTP error from API
                try:
                    error_data = order_response.json()
                    error_msg = error_data.get("message", f"HTTP {order_response.status_code}")
                except:
                    error_msg = f"HTTP {order_response.status_code}: {order_response.text}"
                raise Exception(f"API request failed: {error_msg}")
            
        except Exception as e:
            error_msg = f"❌ **{order.stock_symbol}**: Order failed - {str(e)}"
            execution_details.status = "failed"
            execution_details.error = str(e)
            logger.error(error_msg)
            return execution_details
    
    def log_execution_to_sheet(self, order: RecurringOrder, execution_details: ExecutionDetails):
        """
        Log execution result back to Google Sheets with detailed information.
        
        Args:
            order: Original order dictionary
            success: Whether execution was successful
            message: Execution message (same format as Discord)
            order_id: Order ID if successful
            execution_details: Detailed execution data (same as Discord)
        """
        try:
            spreadsheet = self.sheets_client.open_spreadsheet_by_url(self.sheet_url)
            
            # Try to get the worksheet by the exact name from the Google Sheet
            try:
                worksheet = self.sheets_client.get_worksheet(spreadsheet, 0)  # Use first worksheet
            except Exception:
                # If that fails, try common names
                worksheet_names = ["Recurring Orders - Python", "Sheet1", "Recurring Orders"]
                worksheet = None
                for name in worksheet_names:
                    try:
                        worksheet = spreadsheet.worksheet(name)
                        break
                    except:
                        continue
                
                if not worksheet:
                    logger.error("Could not find appropriate worksheet in Google Sheet")
                    return
            
            # Find the row for this order
            all_records = worksheet.get_all_records()
            symbol = order['Stock Symbol']
            
            # Find the row for this stock symbol
            for i, record in enumerate(all_records, start=2):  # Start at row 2 (header is row 1)
                if record.get(self.column_headers.stock_symbol) == order.stock_symbol:
                    timestamp = datetime.now(pytz.timezone(self._scheduling_config.timezone)).strftime("%Y-%m-%d %H:%M:%S EST")
                    
                    # Create detailed log entry matching Discord format
                    if success and execution_details:
                        # Successful execution with details
                        price = execution_details.get('market_price')
                        quantity = execution_details.get('calculated_quantity', 0)
                        cost = execution_details.get('estimated_cost', 0)
                        
                        log_entry = f"✅ {timestamp}: {symbol} - {quantity} shares"
                        if price:
                            log_entry += f" @ ${price:.2f}"
                        if cost:
                            log_entry += f" (${cost:.2f})"
                        if order_id:
                            log_entry += f" | Order ID: {order_id}"
                        log_entry += f" | Frequency: {order.get(self.column_headers['frequency'], 'Unknown')}"
                        
                    elif success:
                        # Successful execution without details
                        log_entry = f"✅ {timestamp}: {message}"
                        if order_id:
                            log_entry += f" | Order ID: {order_id}"
                            
                    else:
                        # Failed execution
                        error_msg = execution_details.get('error', 'Unknown error') if execution_details else message
                        log_entry = f"❌ {timestamp}: {symbol} - FAILED: {error_msg}"
                        log_entry += f" | Frequency: {order.get(self.column_headers['frequency'], 'Unknown')}"
                    
                    # Get current log content and append
                    current_log = record.get(self.column_headers['log'], '')
                    if current_log:
                        new_log = f"{current_log}\n{log_entry}"
                    else:
                        new_log = log_entry
                    
                    # Also update Last Run column if it exists
                    try:
                        headers = worksheet.row_values(1)
                        # Note: No 'Last Run' column in current sheet structure
                        # Timestamp is now included in the Log column
                        
                        # Update Log column (find it dynamically)
                        log_col = 5  # Default to column E
                        if self.column_headers['log'] in headers:
                            log_col = headers.index(self.column_headers['log']) + 1
                        
                        worksheet.update_cell(i, log_col, new_log)
                        logger.info(f"Updated detailed log for {symbol} in Google Sheets")
                        
                    except Exception as update_error:
                        logger.error(f"Failed to update sheet cells: {update_error}")
                    
                    break
            
        except Exception as e:
            logger.error(f"Failed to log execution to sheet: {e}")
            # Don't raise - logging failure shouldn't stop execution
    
    def send_discord_notification(self, orders_executed: int, successes: int, failures: int, details: List[str], execution_details: List[Dict] = None):
        """
        Send enhanced Discord notification about execution results.
        
        Args:
            orders_executed: Total number of orders processed
            successes: Number of successful orders
            failures: Number of failed orders  
            details: List of execution summary messages
            execution_details: List of detailed execution data dictionaries
        """
        try:
            timestamp = datetime.now(pytz.timezone(self._scheduling_config.timezone)).strftime("%Y-%m-%d %H:%M:%S EST")
            
            # Create embed for Discord
            if failures == 0 and orders_executed > 0:
                color = 0x00ff00  # Green for success
                title = f"🚀 Recurring Orders Executed Successfully"
            elif successes == 0 and orders_executed > 0:
                color = 0xff0000  # Red for all failures
                title = f"❌ Recurring Orders Failed"
            elif orders_executed > 0:
                color = 0xffaa00  # Orange for mixed results
                title = f"⚠️ Recurring Orders Partially Executed"
            else:
                color = 0x0099ff  # Blue for info/status messages
                title = f"📋 IBKR Recurring Orders System"
            
            embed = {
                "title": title,
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "fields": [],
                "footer": {
                    "text": "IBKR Recurring Orders System"
                }
            }
            
            # Add summary if we have actual orders
            if orders_executed > 0:
                embed["fields"].append({
                    "name": "📊 Summary",
                    "value": f"**Total:** {orders_executed}\n**✅ Success:** {successes}\n**❌ Failed:** {failures}",
                    "inline": True
                })
                
                embed["fields"].append({
                    "name": "⏰ Execution Time", 
                    "value": timestamp,
                    "inline": True
                })
                
                # Calculate total investment
                if execution_details:
                    total_invested = sum(
                        detail.get('estimated_cost', 0) 
                        for detail in execution_details 
                        if detail.get('status') == 'success'
                    )
                    if total_invested > 0:
                        embed["fields"].append({
                            "name": "💰 Total Investment",
                            "value": f"${total_invested:.2f}",
                            "inline": True
                        })
            
            # Add detailed order information
            if execution_details:
                order_details = []
                
                for detail in execution_details[:5]:  # Limit to 5 orders for readability
                    symbol = detail.get('symbol', 'Unknown')
                    status = detail.get('status', 'unknown')
                    
                    if status == 'success':
                        price = detail.get('market_price')
                        quantity = detail.get('calculated_quantity', 0)
                        cost = detail.get('estimated_cost', 0)
                        order_id = detail.get('order_id')
                        
                        order_line = f"🟢 **{symbol}**: {quantity} shares"
                        if price:
                            order_line += f" @ ${price:.2f}"
                        if cost:
                            order_line += f" (${cost:.2f})"
                        if order_id:
                            order_line += f"\n   📋 Order ID: `{order_id}`"
                            
                    else:  # failed
                        error = detail.get('error', 'Unknown error')
                        order_line = f"🔴 **{symbol}**: Failed - {error[:50]}{'...' if len(error) > 50 else ''}"
                    
                    order_details.append(order_line)
                
                if order_details:
                    embed["fields"].append({
                        "name": "📋 Order Details",
                        "value": "\n\n".join(order_details),
                        "inline": False
                    })
                    
                    if len(execution_details) > 5:
                        embed["fields"].append({
                            "name": "➕ Additional Orders",
                            "value": f"... and {len(execution_details) - 5} more orders",
                            "inline": False
                        })
            
            # Add general details if no execution details
            elif details:
                details_text = "\n".join(details[:10])
                if len(details) > 10:
                    details_text += f"\n... and {len(details) - 10} more"
                
                embed["fields"].append({
                    "name": "📋 Details",
                    "value": details_text,
                    "inline": False
                })
            
            # Add market hours info for trading notifications
            if orders_executed > 0:
                now_est = datetime.now(EST)
                market_hours = scheduling_config.get('market_hours', {})
                market_open = market_hours.get('market_open_hour', 9)
                market_close = market_hours.get('market_close_hour', 16)
                market_status = "🕘 After Hours" if now_est.hour < market_open or now_est.hour > market_close else "🕘 Market Hours"
                embed["fields"].append({
                    "name": "🏦 Market Status",
                    "value": f"{market_status}\n{now_est.strftime('%A, %B %d, %Y')}",
                    "inline": True
                })
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Enhanced Discord notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    # END OF OLD DISCORD METHOD - TO BE REMOVED
    
    def execute_recurring_orders(self, frequency_filter: Optional[str] = None, manual_trigger: bool = False):
        """
        Execute all active recurring orders for the specified frequency.
        
        Args:
            frequency_filter: If specified, only execute orders with this frequency
            manual_trigger: If True, ignore time-based checks and execute immediately
        """
        logger.info(f"Starting recurring orders execution (manual: {manual_trigger})")
        
        try:
            orders = self.read_recurring_orders()
            
            if not orders:
                logger.info("No active recurring orders found")
                return
            
            # Filter orders by frequency and timing
            orders_to_execute = []
            
            for order in orders:
                frequency = order.frequency.value
                
                # Apply frequency filter if specified
                if frequency_filter and frequency.lower() != frequency_filter.lower():
                    continue
                
                # Check if should execute today (unless manual trigger)
                if not manual_trigger and not self.should_execute_today(frequency):
                    logger.info(f"Skipping {order['Stock Symbol']} - not scheduled for today ({frequency})")
                    continue
                
                orders_to_execute.append(order)
            
            # Always send notification, even if no orders to execute
            if not orders_to_execute:
                logger.info("No orders scheduled for execution today")
                
                # Send "no orders" notification
                now_est = datetime.now(EST)
                active_count = len(orders)
                next_orders = []
                
                # Find when next orders will run
                for order in orders:
                    freq = order.get(self.column_headers['frequency'], '').lower()
                    symbol = order.get(self.column_headers['stock_symbol'], 'Unknown')
                    amount = order.get(self.column_headers['amount'], 0)
                    
                    if freq == 'daily':
                        next_orders.append(f"📅 **{symbol}** (${amount}) - Tomorrow")
                    elif freq == 'weekly' and now_est.weekday() != 0:  # Not Monday
                        days_until_monday = (0 - now_est.weekday() + 7) % 7
                        next_orders.append(f"📅 **{symbol}** (${amount}) - Next Monday")
                    elif freq == 'monthly' and now_est.day != 1:  # Not 1st
                        next_orders.append(f"📅 **{symbol}** (${amount}) - Next Month")
                
                details = [
                    f"📊 **Daily Check Complete** - {now_est.strftime('%A, %B %d, %Y')}",
                    f"🔍 Checked {active_count} active recurring orders",
                    f"✅ No orders scheduled for today",
                    f"⏰ Next check: Tomorrow at {scheduling_config.get('daily_check_time', {}).get('hour', 9)}:00 AM EST"
                ]
                
                if next_orders:
                    details.append("📋 **Upcoming Orders:**")
                    details.extend(next_orders[:3])  # Show up to 3 upcoming orders
                    if len(next_orders) > 3:
                        details.append(f"... and {len(next_orders) - 3} more")
                
                # Send daily check notification
                # Send daily check notification using professional implementation
                try:
                    from .discord_notifier import DiscordNotifier
                    notifier = DiscordNotifier(self.config)
                    notifier.send_simple_notification(
                        message="\n".join(details), 
                        is_error=False
                    )
                    logger.info("✅ Daily check Discord notification sent")
                except Exception as discord_error:
                    logger.error(f"Failed to send daily check Discord notification: {discord_error}")
                
                return
            
            logger.info(f"Executing {len(orders_to_execute)} recurring orders")
            
            # Execute orders
            successes = 0
            failures = 0
            execution_summaries = []
            execution_details_list = []
            
            for order in orders_to_execute:
                execution_details = self.execute_order(order)
                success = execution_details.status == "success"
                message = f"Executed {order.stock_symbol}: {order.qty_to_buy} shares"
                order_id = execution_details.order_id
                
                if success:
                    successes += 1
                else:
                    failures += 1
                
                execution_summaries.append(message)
                execution_details_list.append(execution_details)
                
                # Log to sheet using research-based sequential logging
                try:
                    from .sequential_logger import log_order_execution
                    log_message = log_order_execution(order, execution_details)
                    logger.info(f"✅ Sequential logging successful: {log_message}")
                except Exception as log_error:
                    logger.warning(f"Sequential logging failed: {log_error}")
                
                # Small delay between orders
                import time
                time.sleep(1)
            
            # Send professional Discord notification using research-based implementation
            try:
                from .discord_notifier import send_trading_notification
                send_trading_notification(
                    orders_executed=len(orders_to_execute),
                    successes=successes,
                    failures=failures,
                    execution_details_list=execution_details_list
                )
                logger.info("✅ Professional Discord notification sent successfully")
            except Exception as discord_error:
                logger.error(f"Failed to send Discord notification: {discord_error}")
            
            logger.info(f"Recurring orders execution completed: {successes} success, {failures} failures")
            
            # Always log the daily execution, even if no orders
            if len(orders_to_execute) == 0:
                logger.info("Daily recurring orders check completed - no orders executed")
            
        except Exception as e:
            logger.error(f"Recurring orders execution failed: {e}")
            
            # Send error notification to Discord
            try:
                error_embed = {
                    "title": "💥 Recurring Orders System Error",
                    "description": f"```{str(e)}```",
                    "color": 0xff0000,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {"text": "IBKR Recurring Orders System"}
                }
                requests.post(self.discord_webhook, json={"embeds": [error_embed]}, timeout=10)
            except:
                pass  # Don't fail on notification failure
            
            raise RecurringOrdersError(f"Execution failed: {e}") from e
    
    def start_scheduler(self):
        """Start the APScheduler for automated execution."""
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler = BackgroundScheduler(timezone=EST)
        
        # Schedule daily check (configurable time)
        # This will check for any orders that should run today
        daily_time = scheduling_config.get('daily_check_time', {'hour': 9, 'minute': 0})
        self.scheduler.add_job(
            func=lambda: self.execute_recurring_orders(),
            trigger=CronTrigger(
                hour=daily_time.get('hour', 9), 
                minute=daily_time.get('minute', 0), 
                timezone=EST
            ),
            id='daily_recurring_orders',
            name='Daily Recurring Orders Check',
            misfire_grace_time=scheduling_config.get('grace_time_minutes', 5) * 60  # Grace time from config
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Recurring orders scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Recurring orders scheduler stopped")
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status and next execution times."""
        if not self.scheduler or not self.scheduler.running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }


# --- Convenience Functions ---

def execute_all_recurring_orders(manual: bool = True):
    """Execute all active recurring orders immediately."""
    manager = RecurringOrdersManager()
    manager.execute_recurring_orders(manual_trigger=manual)


def execute_frequency_orders(frequency: str, manual: bool = True):
    """Execute orders for a specific frequency."""
    manager = RecurringOrdersManager()
    manager.execute_recurring_orders(frequency_filter=frequency, manual_trigger=manual)


def start_recurring_scheduler():
    """Start the recurring orders scheduler."""
    manager = RecurringOrdersManager()
    manager.start_scheduler()
    return manager


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='IBKR Recurring Orders System')
    parser.add_argument('--execute', choices=['all', 'daily', 'weekly', 'monthly'], 
                       help='Execute orders immediately')
    parser.add_argument('--start-scheduler', action='store_true', 
                       help='Start the background scheduler')
    parser.add_argument('--status', action='store_true', 
                       help='Show scheduler status')
    
    args = parser.parse_args()
    
    if args.execute:
        if args.execute == 'all':
            execute_all_recurring_orders()
        else:
            execute_frequency_orders(args.execute)
    elif args.start_scheduler:
        manager = start_recurring_scheduler()
        print("Scheduler started. Press Ctrl+C to stop.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_scheduler()
            print("Scheduler stopped.")
    elif args.status:
        manager = RecurringOrdersManager()
        manager.start_scheduler()
        status = manager.get_scheduler_status()
        print(f"Scheduler Status: {status}")
        manager.stop_scheduler()
    else:
        parser.print_help()
