#!/usr/bin/env python3
"""
Discord Trading Notifications

Professional Discord webhook notifications for trading bot executions.
Based on research from trading bot best practices and Discord embed guidelines.
"""

import logging
import requests
from datetime import datetime
from typing import List, Optional

from .config import Config
from .exceptions import NotificationError
from .models import ExecutionDetails, RecurringOrder

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Professional Discord notifications for trading executions."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize Discord notifier."""
        self.config = config or Config()
        discord_config = self.config.get_discord_config()
        self.webhook_url = discord_config.get("webhook_url")
        
        if not self.webhook_url:
            raise NotificationError("Discord webhook URL not configured")
    
    def send_execution_notification(
        self, 
        orders_executed: int,
        successes: int, 
        failures: int,
        execution_details_list: List[ExecutionDetails]
    ) -> None:
        """
        Send professional trading execution notification using rich embeds.
        
        Args:
            orders_executed: Total number of orders processed
            successes: Number of successful executions
            failures: Number of failed executions  
            execution_details_list: List of execution details
        """
        try:
            # Create rich embed based on research best practices
            embed = self._create_execution_embed(
                orders_executed, successes, failures, execution_details_list
            )
            
            payload = {
                "username": "IBKR Trading Bot",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ Discord notification sent successfully")
            else:
                logger.error(f"Discord notification failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise NotificationError(f"Discord notification failed: {e}") from e
    
    def _create_execution_embed(
        self, 
        orders_executed: int, 
        successes: int, 
        failures: int,
        execution_details_list: List[ExecutionDetails]
    ) -> dict:
        """Create professional trading execution embed."""
        
        # Determine embed color based on results
        if failures == 0 and successes > 0:
            color = 0x00FF00  # Green for success
            title = "🚀 Trading Orders Executed Successfully"
        elif failures > 0 and successes > 0:
            color = 0xFFA500  # Orange for mixed results
            title = "⚠️ Trading Orders Executed (Mixed Results)"
        elif failures > 0:
            color = 0xFF0000  # Red for failures
            title = "❌ Trading Order Execution Failed"
        else:
            color = 0x0099FF  # Blue for info
            title = "📊 Trading System Status"
        
        # Create embed structure
        embed = {
            "title": title,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [],
            "footer": {
                "text": "IBKR Recurring Orders System",
                "icon_url": "https://www.interactivebrokers.com/images/2015/ib-logo.png"
            }
        }
        
        # Add summary field
        summary_value = f"**Executed:** {orders_executed}\n**Successful:** {successes}\n**Failed:** {failures}"
        embed["fields"].append({
            "name": "📊 Execution Summary",
            "value": summary_value,
            "inline": True
        })
        
        # Add individual order details (limit to 5 for readability)
        if execution_details_list:
            orders_text = []
            for detail in execution_details_list[:5]:
                if detail.status == "success":
                    price_info = f" @ ${detail.market_price:.2f}" if detail.market_price else ""
                    cost_info = f" (${detail.estimated_cost:.2f})" if detail.estimated_cost else ""
                    order_line = f"✅ **{detail.symbol}**: {detail.target_quantity} shares{price_info}{cost_info}"
                    if detail.order_id:
                        order_line += f"\n   📋 Order ID: `{detail.order_id}`"
                else:
                    error_info = f" - {detail.error[:50]}..." if detail.error and len(detail.error) > 50 else f" - {detail.error}" if detail.error else ""
                    order_line = f"❌ **{detail.symbol}**: Failed{error_info}"
                
                orders_text.append(order_line)
            
            if orders_text:
                embed["fields"].append({
                    "name": "📋 Order Details",
                    "value": "\n\n".join(orders_text),
                    "inline": False
                })
        
        # Add timestamp field
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p EST")
        embed["fields"].append({
            "name": "🕐 Execution Time",
            "value": current_time,
            "inline": True
        })
        
        return embed
    
    def send_simple_notification(self, message: str, is_error: bool = False) -> None:
        """
        Send a simple notification message.
        
        Args:
            message: Message to send
            is_error: Whether this is an error message
        """
        try:
            color = 0xFF0000 if is_error else 0x0099FF
            title = "❌ System Error" if is_error else "📊 System Notification"
            
            embed = {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "IBKR Recurring Orders System"
                }
            }
            
            payload = {
                "username": "IBKR Trading Bot",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ Discord simple notification sent")
            else:
                logger.error(f"Discord notification failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send simple Discord notification: {e}")


def send_trading_notification(
    orders_executed: int,
    successes: int,
    failures: int, 
    execution_details_list: List[ExecutionDetails]
) -> None:
    """
    Convenience function to send trading execution notification.
    
    Args:
        orders_executed: Total orders processed
        successes: Successful executions
        failures: Failed executions
        execution_details_list: List of execution details
    """
    notifier = DiscordNotifier()
    notifier.send_execution_notification(orders_executed, successes, failures, execution_details_list)
