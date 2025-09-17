#!/usr/bin/env python3
"""
Test the Recurring Orders System

This script tests the key functionality of the recurring orders system
without placing actual trades.
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """Test that all imports work correctly."""
    print("🔧 Testing imports...")
    
    try:
        from backend.recurring_orders import RecurringOrdersManager, RecurringOrdersError
        from backend.api_recurring import recurring_bp
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_google_sheets_connection():
    """Test Google Sheets connection."""
    print("\n📊 Testing Google Sheets connection...")
    
    try:
        from backend.sheets_integration import get_sheets_client
        
        sheets = get_sheets_client()
        url = "https://docs.google.com/spreadsheets/d/1CwyNMN_YRhU5IaYaG1OXaBGzgoYkBtF5rc9sO9Nyw48/edit"
        
        spreadsheet = sheets.open_spreadsheet_by_url(url)
        worksheet = sheets.get_worksheet(spreadsheet, "Recurring Orders - Python")
        
        orders = sheets.read_all_records(worksheet)
        print(f"✅ Google Sheets connection successful - found {len(orders)} orders")
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}")
        return False

def test_recurring_manager():
    """Test RecurringOrdersManager functionality."""
    print("\n🤖 Testing RecurringOrdersManager...")
    
    try:
        from backend.recurring_orders import RecurringOrdersManager
        
        # Test initialization (without IBKR client for now)
        manager = RecurringOrdersManager()
        
        # Test reading orders
        orders = manager.read_recurring_orders()
        print(f"✅ Read {len(orders)} active recurring orders")
        
        # Test timing logic
        should_daily = manager.should_execute_today('Daily')
        should_weekly = manager.should_execute_today('Weekly') 
        should_monthly = manager.should_execute_today('Monthly')
        
        print(f"✅ Timing logic: Daily={should_daily}, Weekly={should_weekly}, Monthly={should_monthly}")
        
        return True
        
    except Exception as e:
        print(f"❌ RecurringOrdersManager test failed: {e}")
        return False

def test_discord_notification():
    """Test Discord notification functionality."""
    print("\n📢 Testing Discord notification...")
    
    try:
        from backend.recurring_orders import RecurringOrdersManager
        
        manager = RecurringOrdersManager()
        
        # Send test notification
        manager.send_discord_notification(
            orders_executed=0,
            successes=0, 
            failures=0,
            details=["🧪 Test notification from recurring orders system"]
        )
        
        print("✅ Discord notification sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Discord notification failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are properly registered."""
    print("\n🌐 Testing API endpoint registration...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from backend.api import app
        
        # Check if recurring blueprint is registered
        blueprints = [bp.name for bp in app.blueprints.values()]
        
        if 'recurring' in blueprints:
            print("✅ Recurring orders blueprint registered")
            
            # Test client creation
            with app.test_client() as client:
                # Test status endpoint
                response = client.get('/recurring/status')
                print(f"✅ Status endpoint responded with code: {response.status_code}")
                
            return True
        else:
            print("❌ Recurring orders blueprint not found")
            return False
            
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_cron_setup():
    """Test cron setup script."""
    print("\n⏰ Testing cron setup...")
    
    try:
        tools_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools')
        sys.path.append(tools_path)
        from setup_cron import create_cron_script, setup_log_directory
        
        # Test script creation
        script_path = create_cron_script()
        if script_path.exists():
            print(f"✅ Cron script created: {script_path}")
        
        # Test log directory creation
        log_dir = setup_log_directory()
        if log_dir.exists():
            print(f"✅ Log directory created: {log_dir}")
            
        return True
        
    except Exception as e:
        print(f"❌ Cron setup test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 IBKR Recurring Orders System - Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_google_sheets_connection,
        test_recurring_manager,
        test_discord_notification, 
        test_api_endpoints,
        test_cron_setup
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Recurring orders system is ready.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
