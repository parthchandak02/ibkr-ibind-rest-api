#!/usr/bin/env python3
"""
IBKR Recurring Orders - Persistent Service

This runs as a persistent background service (like PM2 for Node.js) and 
automatically executes recurring orders based on schedule.

Features:
- Always running, no missed executions
- Real-time health monitoring
- Automatic error recovery
- Graceful shutdown handling
- Service status API
"""

import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify
from threading import Thread

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.recurring_orders import RecurringOrdersManager, RecurringOrdersError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/recurring_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Timezone
EST = pytz.timezone('US/Eastern')

class RecurringOrdersService:
    """
    Persistent service for recurring orders execution.
    
    This is the Python equivalent of PM2 for our trading system.
    """
    
    def __init__(self):
        self.scheduler = None
        self.manager = None
        self.flask_app = None
        self.flask_thread = None
        self.is_running = False
        self.startup_time = None
        
        # Service statistics
        self.stats = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "last_execution": None,
            "last_error": None,
            "uptime_start": None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
    
    def initialize(self):
        """Initialize the service components."""
        try:
            logger.info("🚀 Initializing IBKR Recurring Orders Service...")
            
            # Initialize recurring orders manager
            self.manager = RecurringOrdersManager()
            logger.info("✅ Recurring orders manager initialized")
            
            # Initialize scheduler
            self.scheduler = BlockingScheduler(timezone=EST)
            
            # Schedule daily execution at 9:00 AM EST
            self.scheduler.add_job(
                func=self.execute_daily_check,
                trigger=CronTrigger(hour=9, minute=0, timezone=EST),
                id='daily_recurring_orders',
                name='Daily Recurring Orders Execution',
                misfire_grace_time=300,  # 5 minutes grace time
                max_instances=1
            )
            
            # Schedule health check every 5 minutes
            self.scheduler.add_job(
                func=self.health_check,
                trigger=CronTrigger(minute='*/5'),
                id='health_check',
                name='Service Health Check',
                misfire_grace_time=60,
                max_instances=1
            )
            
            # Schedule hourly status report
            self.scheduler.add_job(
                func=self.hourly_status,
                trigger=CronTrigger(minute=0),
                id='hourly_status', 
                name='Hourly Status Report',
                misfire_grace_time=120,
                max_instances=1
            )
            
            logger.info("✅ Scheduler configured with 3 jobs")
            
            # Initialize status API
            self.setup_status_api()
            
            self.startup_time = datetime.now(EST)
            self.stats["uptime_start"] = self.startup_time
            
            logger.info("🎉 Service initialization complete!")
            
        except Exception as e:
            logger.error(f"💥 Service initialization failed: {e}")
            raise
    
    def setup_status_api(self):
        """Setup lightweight Flask API for service status."""
        self.flask_app = Flask(__name__)
        
        @self.flask_app.route('/service/status')
        def service_status():
            """Get service status and statistics."""
            uptime = None
            if self.stats["uptime_start"]:
                uptime_delta = datetime.now(EST) - self.stats["uptime_start"]
                uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
            
            next_executions = []
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    next_executions.append({
                        "job": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                    })
            
            return jsonify({
                "service": "IBKR Recurring Orders",
                "status": "running" if self.is_running else "stopped",
                "uptime": uptime,
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "statistics": self.stats,
                "next_executions": next_executions,
                "scheduler_running": self.scheduler.running if self.scheduler else False,
                "timestamp": datetime.now(EST).isoformat()
            })
        
        @self.flask_app.route('/service/execute', methods=['POST'])
        def manual_execute():
            """Manually trigger execution."""
            try:
                self.execute_daily_check(manual=True)
                return jsonify({"status": "success", "message": "Manual execution triggered"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.flask_app.route('/service/health')
        def service_health():
            """Simple health check endpoint."""
            return jsonify({
                "status": "healthy" if self.is_running else "unhealthy",
                "timestamp": datetime.now(EST).isoformat()
            })
    
    def start_status_api(self):
        """Start the Flask status API in a separate thread."""
        def run_flask():
            from backend.config import Config
            config = Config()
            port = config.get_settings()["service_port"]  # No fallback - config.json required
            self.flask_app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
        
        self.flask_thread = Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        logger.info(f"📊 Status API started on http://127.0.0.1:{port}")
    
    def execute_daily_check(self, manual=False):
        """Execute the daily recurring orders check."""
        execution_start = datetime.now(EST)
        logger.info(f"🔄 Starting daily orders check (manual: {manual})")
        
        try:
            self.stats["executions"] += 1
            
            # Execute recurring orders
            self.manager.execute_recurring_orders(manual_trigger=manual)
            
            self.stats["successes"] += 1
            self.stats["last_execution"] = execution_start.isoformat()
            
            logger.info("✅ Daily orders check completed successfully")
            
        except Exception as e:
            self.stats["failures"] += 1
            self.stats["last_error"] = {
                "timestamp": execution_start.isoformat(),
                "error": str(e)
            }
            
            logger.error(f"❌ Daily orders check failed: {e}")
            
            # Send error notification
            try:
                self.manager.send_discord_notification(
                    orders_executed=0,
                    successes=0,
                    failures=1,
                    details=[f"💥 Service Error: {str(e)}"],
                    execution_details=None
                )
            except:
                pass  # Don't fail on notification failure
    
    def health_check(self):
        """Perform periodic health check."""
        try:
            # Check if manager is still functional
            if self.manager:
                orders = self.manager.read_recurring_orders()
                logger.debug(f"🏥 Health check: {len(orders)} active orders found")
            else:
                logger.warning("⚠️ Health check: Manager not initialized")
                
        except Exception as e:
            logger.error(f"💔 Health check failed: {e}")
    
    def hourly_status(self):
        """Send hourly status update."""
        try:
            uptime_delta = datetime.now(EST) - self.stats["uptime_start"]
            uptime_str = str(uptime_delta).split('.')[0]
            
            # Read current orders
            orders = self.manager.read_recurring_orders()
            
            status_msg = (
                f"📊 **Hourly Status Report**\n"
                f"⏰ Uptime: {uptime_str}\n"
                f"📈 Executions: {self.stats['executions']} "
                f"(✅ {self.stats['successes']} / ❌ {self.stats['failures']})\n"
                f"📋 Active Orders: {len(orders)}\n"
                f"🕘 Next Check: Tomorrow 9:00 AM EST"
            )
            
            # Only send status during business hours to avoid spam
            current_hour = datetime.now(EST).hour
            if 6 <= current_hour <= 20:  # 6 AM to 8 PM EST
                self.manager.send_discord_notification(
                    orders_executed=0,
                    successes=0,
                    failures=0,
                    details=[status_msg],
                    execution_details=None
                )
            
        except Exception as e:
            logger.error(f"📊 Hourly status failed: {e}")
    
    def start(self):
        """Start the service."""
        try:
            logger.info("🚀 Starting IBKR Recurring Orders Service...")
            
            self.initialize()
            self.is_running = True
            
            # Start status API
            self.start_status_api()
            
            # Send startup notification
            try:
                self.manager.send_discord_notification(
                    orders_executed=0,
                    successes=0,
                    failures=0,
                    details=[
                        "🚀 **IBKR Recurring Orders Service Started**",
                        f"⏰ Started at: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S EST')}",
                        "📅 Next execution: Tomorrow 9:00 AM EST",
                        f"📊 Status API: http://127.0.0.1:{config.get_settings()['service_port']}/service/status"
                    ],
                    execution_details=None
                )
            except:
                pass  # Don't fail startup on notification failure
            
            logger.info("🎉 Service started successfully! Running scheduler...")
            
            # Start the scheduler (this blocks)
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("👋 Service interrupted by user")
            self.shutdown()
        except Exception as e:
            logger.error(f"💥 Service startup failed: {e}")
            self.shutdown()
            raise
    
    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the service."""
        logger.info("🛑 Shutting down service...")
        
        self.is_running = False
        
        # Stop scheduler
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("⏹️ Scheduler stopped")
        
        # Send shutdown notification
        try:
            if self.manager:
                uptime_delta = datetime.now(EST) - self.stats["uptime_start"]
                uptime_str = str(uptime_delta).split('.')[0]
                
                self.manager.send_discord_notification(
                    orders_executed=0,
                    successes=0,
                    failures=0,
                    details=[
                        "🛑 **IBKR Recurring Orders Service Stopped**",
                        f"⏰ Uptime: {uptime_str}",
                        f"📊 Total Executions: {self.stats['executions']}",
                        f"✅ Successes: {self.stats['successes']} | ❌ Failures: {self.stats['failures']}"
                    ],
                    execution_details=None
                )
        except:
            pass  # Don't fail shutdown on notification failure
        
        logger.info("👋 Service shutdown complete")


def main():
    """Main service entry point."""
    print("🚀 IBKR Recurring Orders Service")
    print("=" * 50)
    print("This service runs continuously and executes")
    print("recurring orders based on your Google Sheets.")
    print("=" * 50)
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Create and start service
    service = RecurringOrdersService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"\n💥 Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
