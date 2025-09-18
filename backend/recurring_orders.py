#!/usr/bin/env python3
"""
Recurring Orders System for IBKR Trading API

This module provides automated recurring order execution based on Google Sheets data.
Supports Daily, Weekly, and Monthly scheduling with EST timezone handling.

Features:
- APScheduler for robust scheduling
- Discord webhook notifications  
- Google Sheets integration for order management
- IBKR API integration for order execution
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

from .utils import get_ibkr_client
from .sheets_integration import get_sheets_client
from .trading_operations import resolve_symbol_to_conid, SymbolResolutionError
from ibind import make_order_request, QuestionType

logger = logging.getLogger(__name__)

# --- Configuration ---
from .config import Config

# Load configuration
config = Config()
google_sheets_config = config.get_google_sheets_config()
discord_config = config.get_discord_config()
settings = config.get_settings()

DISCORD_WEBHOOK_URL = discord_config.get("webhook_url", os.getenv("DISCORD_WEBHOOK_URL"))
SHEET_URL = google_sheets_config.get("spreadsheet_url", os.getenv("GOOGLE_SHEET_URL"))
EST = pytz.timezone('US/Eastern')

# Scheduling Configuration
SCHEDULE_CONFIG = {
    'Daily': {'hour': 9, 'minute': 0},      # 9:00 AM EST
    'Weekly': {'day_of_week': 0, 'hour': 9, 'minute': 0},  # Monday 9:00 AM EST  
    'Monthly': {'day': 1, 'hour': 9, 'minute': 0}  # 1st of month 9:00 AM EST
}


class RecurringOrdersError(Exception):
    """Custom exception for recurring orders system."""
    pass


class RecurringOrdersManager:
    """
    Manages automated recurring orders from Google Sheets.
    
    Handles scheduling, execution, logging, and notifications.
    """
    
    def __init__(self, sheet_url: str = SHEET_URL, discord_webhook: str = DISCORD_WEBHOOK_URL):
        self.sheet_url = sheet_url
        self.discord_webhook = discord_webhook
        self.scheduler = None
        self.sheets_client = None
        self.ibkr_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Google Sheets and IBKR clients."""
        try:
            self.sheets_client = get_sheets_client()
            self.ibkr_client = get_ibkr_client()
            
            if not self.ibkr_client:
                raise RecurringOrdersError("IBKR client initialization failed")
                
            # Ensure account ID is set
            if not self.ibkr_client.account_id:
                accounts = self.ibkr_client.portfolio_accounts().data
                if accounts and len(accounts) > 0:
                    self.ibkr_client.account_id = accounts[0]["accountId"]
                else:
                    raise RecurringOrdersError("No IBKR account ID available")
                    
            logger.info("Successfully initialized all clients")
            
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
            
            orders = self.sheets_client.read_all_records(worksheet)
            
            # Filter for active orders only
            active_orders = [
                order for order in orders 
                if order.get('Status', '').lower() == 'active' and 
                   order.get('Stock Symbol') and 
                   order.get('Amount (USD)') and 
                   order.get('Frequency')
            ]
            
            logger.info(f"Read {len(active_orders)} active recurring orders")
            return active_orders
            
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
        Execute a single recurring order with detailed tracking.
        
        Args:
            order: Order dictionary from Google Sheets
            
        Returns:
            Tuple of (success, message, order_id, execution_details)
        """
        symbol = order['Stock Symbol'].upper()
        amount_usd = float(order['Amount (USD)'])
        execution_details = {
            "symbol": symbol,
            "target_amount": amount_usd,
            "timestamp": datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST"),
            "frequency": order.get('Frequency', 'Unknown')
        }
        
        try:
            # Resolve symbol to contract ID
            conid = resolve_symbol_to_conid(self.ibkr_client, symbol)
            logger.info(f"Resolved {symbol} to conid: {conid}")
            execution_details["conid"] = conid
            
            # Get current market price for better quantity calculation
            try:
                from .market_data import get_current_price_for_symbol
                current_price = get_current_price_for_symbol(symbol, conid)
                execution_details["market_price"] = current_price
                
                # Calculate quantity based on current price
                quantity = max(1, int(amount_usd / current_price))
                actual_cost = quantity * current_price
                execution_details["calculated_quantity"] = quantity
                execution_details["estimated_cost"] = actual_cost
                
            except Exception as price_error:
                logger.warning(f"Could not get current price for {symbol}: {price_error}")
                # Fallback to simple calculation
                quantity = max(1, int(amount_usd / 100))  # Rough estimate
                execution_details["market_price"] = None
                execution_details["calculated_quantity"] = quantity
                execution_details["estimated_cost"] = amount_usd
            
            # Create order tag with timestamp
            order_tag = f'recurring-{symbol}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            execution_details["order_tag"] = order_tag
            
            order_request = make_order_request(
                conid=int(conid),
                side="BUY",
                quantity=quantity,
                order_type="MKT",
                acct_id=self.ibkr_client.account_id,
                coid=order_tag,
                tif="DAY"
            )
            
            answers = {
                QuestionType.UNFORESEEN_NEW_QUESTION: True,
                QuestionType.MARKET_ORDER_CONFIRMATION: True,
            }
            
            # Execute the order
            response = self.ibkr_client.place_order(order_request, answers).data
            execution_details["ibkr_response"] = response
            
            # Extract order ID if available
            order_id = None
            if isinstance(response, list) and len(response) > 0:
                order_data = response[0]
                order_id = order_data.get('order_id') or order_data.get('orderId')
                execution_details["order_id"] = order_id
            
            # Create detailed success message
            price_info = f" @ ~${execution_details['market_price']:.2f}" if execution_details['market_price'] else ""
            cost_info = f" (~${execution_details['estimated_cost']:.2f})" if execution_details['estimated_cost'] else ""
            
            success_msg = f"✅ **{symbol}**: {quantity} shares{price_info}{cost_info}"
            if order_id:
                success_msg += f" | Order ID: {order_id}"
            
            execution_details["status"] = "success"
            execution_details["message"] = success_msg
            
            logger.info(f"Order placed successfully: {order_tag}")
            
            return True, success_msg, order_tag, execution_details
            
        except SymbolResolutionError as e:
            error_msg = f"❌ **{symbol}**: Symbol resolution failed - {str(e)}"
            execution_details["status"] = "failed"
            execution_details["error"] = str(e)
            execution_details["message"] = error_msg
            logger.error(error_msg)
            return False, error_msg, None, execution_details
            
        except Exception as e:
            error_msg = f"❌ **{symbol}**: Order failed - {str(e)}"
            execution_details["status"] = "failed"
            execution_details["error"] = str(e)
            execution_details["message"] = error_msg
            logger.error(error_msg)
            return False, error_msg, None, execution_details
    
    def log_execution_to_sheet(self, order: Dict, success: bool, message: str, order_id: Optional[str], execution_details: Optional[Dict] = None):
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
            
            for i, record in enumerate(all_records, start=2):  # Start at row 2 (header is row 1)
                if record.get('Stock Symbol') == symbol:
                    timestamp = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
                    
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
                        log_entry += f" | Frequency: {order.get('Frequency', 'Unknown')}"
                        
                    elif success:
                        # Successful execution without details
                        log_entry = f"✅ {timestamp}: {message}"
                        if order_id:
                            log_entry += f" | Order ID: {order_id}"
                            
                    else:
                        # Failed execution
                        error_msg = execution_details.get('error', 'Unknown error') if execution_details else message
                        log_entry = f"❌ {timestamp}: {symbol} - FAILED: {error_msg}"
                        log_entry += f" | Frequency: {order.get('Frequency', 'Unknown')}"
                    
                    # Get current log content and append
                    current_log = record.get('Log', '')
                    if current_log:
                        new_log = f"{current_log}\n{log_entry}"
                    else:
                        new_log = log_entry
                    
                    # Also update Last Run column if it exists
                    try:
                        headers = worksheet.row_values(1)
                        if 'Last Run' in headers:
                            last_run_col = headers.index('Last Run') + 1
                            worksheet.update_cell(i, last_run_col, timestamp)
                        
                        # Update Log column (find it dynamically)
                        log_col = 5  # Default to column E
                        if 'Log' in headers:
                            log_col = headers.index('Log') + 1
                        
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
            timestamp = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
            
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
                market_status = "🕘 After Hours" if now_est.hour < 9 or now_est.hour > 16 else "🕘 Market Hours"
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
                frequency = order['Frequency']
                
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
                    freq = order.get('Frequency', '').lower()
                    symbol = order.get('Stock Symbol', 'Unknown')
                    amount = order.get('Amount (USD)', 0)
                    
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
                    f"⏰ Next check: Tomorrow at 9:00 AM EST"
                ]
                
                if next_orders:
                    details.append("📋 **Upcoming Orders:**")
                    details.extend(next_orders[:3])  # Show up to 3 upcoming orders
                    if len(next_orders) > 3:
                        details.append(f"... and {len(next_orders) - 3} more")
                
                # Send daily check notification
                self.send_discord_notification(
                    orders_executed=0,
                    successes=0,
                    failures=0,
                    details=details,
                    execution_details=None
                )
                
                return
            
            logger.info(f"Executing {len(orders_to_execute)} recurring orders")
            
            # Execute orders
            successes = 0
            failures = 0
            execution_summaries = []
            execution_details = []
            
            for order in orders_to_execute:
                success, message, order_id, detail_data = self.execute_order(order)
                
                if success:
                    successes += 1
                else:
                    failures += 1
                
                execution_summaries.append(message)
                if detail_data:
                    execution_details.append(detail_data)
                
                # Log to sheet with detailed information (same as Discord)
                self.log_execution_to_sheet(order, success, message, order_id, detail_data)
                
                # Small delay between orders
                import time
                time.sleep(1)
            
            # Send enhanced Discord notification with detailed execution data
            self.send_discord_notification(
                orders_executed=len(orders_to_execute),
                successes=successes,
                failures=failures,
                details=execution_summaries,
                execution_details=execution_details
            )
            
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
        
        # Schedule daily check at 9:00 AM EST
        # This will check for any orders that should run today
        self.scheduler.add_job(
            func=lambda: self.execute_recurring_orders(),
            trigger=CronTrigger(hour=9, minute=0, timezone=EST),
            id='daily_recurring_orders',
            name='Daily Recurring Orders Check',
            misfire_grace_time=300  # 5 minutes grace time
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
