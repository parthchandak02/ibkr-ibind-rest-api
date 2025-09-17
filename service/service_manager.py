#!/usr/bin/env python3
"""
Service Manager for IBKR Recurring Orders

Python equivalent to PM2 - manages the recurring orders service lifecycle.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
import requests

class ServiceManager:
    """Manages the IBKR Recurring Orders service."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.service_script = Path(__file__).parent / "recurring_orders_service.py"
        self.pid_file = self.project_root / "logs" / "service.pid"
        self.logs_dir = self.project_root / "logs"
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
    
    def start(self, daemon=True):
        """Start the service."""
        if self.is_running():
            print("✅ Service is already running")
            return True
        
        print("🚀 Starting IBKR Recurring Orders Service...")
        
        try:
            if daemon:
                # Start as daemon process
                process = subprocess.Popen([
                    sys.executable, str(self.service_script)
                ], 
                cwd=self.project_root,
                stdout=open(self.logs_dir / "service_stdout.log", "w"),
                stderr=open(self.logs_dir / "service_stderr.log", "w"),
                start_new_session=True
                )
                
                # Save PID
                with open(self.pid_file, "w") as f:
                    f.write(str(process.pid))
                
                # Wait a moment to check if it started successfully
                time.sleep(3)
                
                if self.is_running():
                    print(f"✅ Service started successfully (PID: {process.pid})")
                    print(f"📊 Status API: http://127.0.0.1:8081/service/status")
                    print(f"📋 Logs: {self.logs_dir}/recurring_service.log")
                    return True
                else:
                    print("❌ Service failed to start")
                    return False
            else:
                # Start in foreground
                process = subprocess.run([
                    sys.executable, str(self.service_script)
                ], cwd=self.project_root)
                return process.returncode == 0
                
        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def stop(self):
        """Stop the service."""
        if not self.is_running():
            print("⚠️ Service is not running")
            return True
        
        print("🛑 Stopping service...")
        
        try:
            pid = self.get_pid()
            if pid:
                process = psutil.Process(pid)
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print("✅ Service stopped gracefully")
                except psutil.TimeoutExpired:
                    print("⚠️ Service didn't stop gracefully, forcing...")
                    process.kill()
                    print("✅ Service force-stopped")
                
                # Remove PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                
                return True
            
        except Exception as e:
            print(f"❌ Error stopping service: {e}")
            return False
    
    def restart(self):
        """Restart the service."""
        print("🔄 Restarting service...")
        self.stop()
        time.sleep(2)
        return self.start()
    
    def status(self):
        """Get service status."""
        if not self.is_running():
            print("❌ Service is NOT running")
            return False
        
        print("✅ Service is running")
        
        try:
            pid = self.get_pid()
            if pid:
                process = psutil.Process(pid)
                print(f"📊 PID: {pid}")
                print(f"⏰ Started: {time.ctime(process.create_time())}")
                print(f"💾 Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
                print(f"🔢 CPU: {process.cpu_percent():.1f}%")
            
            # Try to get detailed status from API
            try:
                response = requests.get("http://127.0.0.1:8081/service/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"🏥 Status API: ✅ Healthy")
                    print(f"⏱️ Uptime: {data.get('uptime', 'Unknown')}")
                    print(f"🎯 Executions: {data.get('statistics', {}).get('executions', 0)}")
                    print(f"✅ Successes: {data.get('statistics', {}).get('successes', 0)}")
                    print(f"❌ Failures: {data.get('statistics', {}).get('failures', 0)}")
                    
                    next_exec = data.get('next_executions', [])
                    if next_exec:
                        print("📅 Next executions:")
                        for job in next_exec:
                            print(f"   • {job['job']}: {job['next_run']}")
                else:
                    print(f"⚠️ Status API: HTTP {response.status_code}")
                    
            except requests.RequestException:
                print("⚠️ Status API: Not responding")
            
            return True
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return False
    
    def logs(self, follow=False, lines=50):
        """Show service logs."""
        log_file = self.logs_dir / "recurring_service.log"
        
        if not log_file.exists():
            print("❌ Log file not found")
            return
        
        if follow:
            print(f"📋 Following logs from {log_file}")
            print("   Press Ctrl+C to stop")
            try:
                subprocess.run(["tail", "-f", str(log_file)])
            except KeyboardInterrupt:
                print("\n👋 Stopped following logs")
        else:
            print(f"📋 Last {lines} lines from {log_file}")
            subprocess.run(["tail", "-n", str(lines), str(log_file)])
    
    def execute(self):
        """Manually trigger execution."""
        try:
            response = requests.post("http://127.0.0.1:8081/service/execute", timeout=10)
            if response.status_code == 200:
                print("✅ Manual execution triggered successfully")
                return True
            else:
                print(f"❌ Manual execution failed: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Could not connect to service: {e}")
            return False
    
    def is_running(self):
        """Check if service is running."""
        pid = self.get_pid()
        if not pid:
            return False
        
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            # Clean up stale PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def get_pid(self):
        """Get service PID."""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file) as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None
    
    def install_systemd(self):
        """Install systemd service (Linux only)."""
        if os.name != 'posix':
            print("❌ systemd is only available on Linux")
            return False
        
        service_content = f"""[Unit]
Description=IBKR Recurring Orders Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'user')}
WorkingDirectory={self.project_root}
Environment=GOOGLE_SHEETS_CREDENTIALS_PATH={self.project_root}/google_sheets_credentials.json
ExecStart={sys.executable} {self.service_script}
Restart=always
RestartSec=10
StandardOutput=append:{self.logs_dir}/service_stdout.log
StandardError=append:{self.logs_dir}/service_stderr.log

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/etc/systemd/system/ibkr-recurring-orders.service"
        
        try:
            print(f"📝 Installing systemd service to {service_file}")
            with open("/tmp/ibkr-recurring-orders.service", "w") as f:
                f.write(service_content)
            
            print("🔧 Run these commands as root:")
            print(f"sudo cp /tmp/ibkr-recurring-orders.service {service_file}")
            print("sudo systemctl daemon-reload")
            print("sudo systemctl enable ibkr-recurring-orders")
            print("sudo systemctl start ibkr-recurring-orders")
            print("")
            print("📊 Monitor with:")
            print("sudo systemctl status ibkr-recurring-orders")
            print("sudo journalctl -u ibkr-recurring-orders -f")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create systemd service: {e}")
            return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="IBKR Recurring Orders Service Manager")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the service')
    start_parser.add_argument('--foreground', action='store_true', 
                             help='Run in foreground instead of daemon mode')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the service')
    
    # Restart command
    subparsers.add_parser('restart', help='Restart the service')
    
    # Status command
    subparsers.add_parser('status', help='Show service status')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show service logs')
    logs_parser.add_argument('-f', '--follow', action='store_true', 
                            help='Follow log output')
    logs_parser.add_argument('-n', '--lines', type=int, default=50,
                            help='Number of lines to show (default: 50)')
    
    # Execute command
    subparsers.add_parser('execute', help='Manually trigger execution')
    
    # Install command
    subparsers.add_parser('install-systemd', help='Install systemd service (Linux)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ServiceManager()
    
    if args.command == 'start':
        manager.start(daemon=not args.foreground)
    elif args.command == 'stop':
        manager.stop()
    elif args.command == 'restart':
        manager.restart()
    elif args.command == 'status':
        manager.status()
    elif args.command == 'logs':
        manager.logs(follow=args.follow, lines=args.lines)
    elif args.command == 'execute':
        manager.execute()
    elif args.command == 'install-systemd':
        manager.install_systemd()


if __name__ == "__main__":
    main()
