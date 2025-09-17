#!/usr/bin/env python3
"""
API Endpoints for Recurring Orders System

Extends the main Flask API with recurring order management endpoints.
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from .recurring_orders import RecurringOrdersManager, RecurringOrdersError

logger = logging.getLogger(__name__)

# Create Blueprint for recurring orders
recurring_bp = Blueprint('recurring', __name__, url_prefix='/recurring')

# Global manager instance
_manager = None


def get_manager():
    """Get or create the recurring orders manager."""
    global _manager
    if _manager is None:
        _manager = RecurringOrdersManager()
    return _manager


# ======================
# RECURRING ORDER ENDPOINTS
# ======================

@recurring_bp.route('/status', methods=['GET'])
def get_status():
    """Get recurring orders system status."""
    try:
        manager = get_manager()
        
        # Get scheduler status
        scheduler_status = manager.get_scheduler_status()
        
        # Get active orders from sheet
        orders = manager.read_recurring_orders()
        
        # Count by frequency
        frequency_counts = {}
        for order in orders:
            freq = order.get('Frequency', 'Unknown')
            frequency_counts[freq] = frequency_counts.get(freq, 0) + 1
        
        return jsonify({
            "status": "ok",
            "scheduler": scheduler_status,
            "active_orders": len(orders),
            "frequency_breakdown": frequency_counts,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@recurring_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all active recurring orders from the sheet."""
    try:
        manager = get_manager()
        orders = manager.read_recurring_orders()
        
        return jsonify({
            "status": "ok",
            "orders": orders,
            "count": len(orders)
        })
        
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@recurring_bp.route('/execute', methods=['POST'])
def execute_orders():
    """Execute recurring orders manually."""
    try:
        data = request.json or {}
        frequency_filter = data.get('frequency')  # Optional: 'daily', 'weekly', 'monthly'
        
        manager = get_manager()
        
        # Execute orders with manual trigger
        manager.execute_recurring_orders(
            frequency_filter=frequency_filter,
            manual_trigger=True
        )
        
        return jsonify({
            "status": "ok",
            "message": "Recurring orders executed successfully",
            "frequency_filter": frequency_filter,
            "timestamp": datetime.now().isoformat()
        })
        
    except RecurringOrdersError as e:
        logger.error(f"Recurring orders execution failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error executing orders: {e}")
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500


@recurring_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the recurring orders scheduler."""
    try:
        manager = get_manager()
        manager.start_scheduler()
        
        return jsonify({
            "status": "ok",
            "message": "Scheduler started successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@recurring_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the recurring orders scheduler."""
    try:
        manager = get_manager()
        manager.stop_scheduler()
        
        return jsonify({
            "status": "ok",
            "message": "Scheduler stopped successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@recurring_bp.route('/test-notification', methods=['POST'])
def test_notification():
    """Test Discord notification."""
    try:
        manager = get_manager()
        
        # Send test notification
        manager.send_discord_notification(
            orders_executed=0,
            successes=0,
            failures=0,
            details=["🧪 Test notification from IBKR Recurring Orders API"]
        )
        
        return jsonify({
            "status": "ok",
            "message": "Test notification sent to Discord"
        })
        
    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
