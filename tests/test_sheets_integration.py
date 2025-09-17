#!/usr/bin/env python3
"""
Test script for Google Sheets integration.
Run this to verify your setup is working correctly.
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append('backend')

from sheets_integration import get_sheets_client


def test_authentication():
    """Test if we can authenticate with Google Sheets."""
    print("🔐 Testing authentication...")
    
    try:
        sheets = get_sheets_client()
        print("✅ Authentication successful!")
        return sheets
    except FileNotFoundError:
        print("❌ Credentials file not found!")
        print("   Place 'google_sheets_credentials.json' in the project root")
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def test_sheet_access(sheets, sheet_url):
    """Test if we can access the specified sheet."""
    print("📊 Testing sheet access...")
    
    try:
        spreadsheet = sheets.open_spreadsheet_by_url(sheet_url)
        print(f"✅ Successfully opened: {spreadsheet.title}")
        
        # Get first worksheet
        worksheet = sheets.get_worksheet(spreadsheet, index=0)
        print(f"✅ Accessed worksheet: {worksheet.title}")
        
        return spreadsheet, worksheet
    except Exception as e:
        print(f"❌ Failed to access sheet: {e}")
        print("   Make sure:")
        print("   1. The sheet URL is correct")
        print("   2. You've shared the sheet with your service account email")
        print("   3. The service account has 'Editor' permissions")
        return None, None


def test_read_data(sheets, worksheet):
    """Test reading data from the sheet."""
    print("📖 Testing data reading...")
    
    try:
        # Try to read all records
        data = sheets.read_all_records(worksheet)
        print(f"✅ Successfully read {len(data)} records")
        
        if data:
            print("   Sample record:", data[0])
        
        return True
    except Exception as e:
        print(f"❌ Failed to read data: {e}")
        return False


def test_write_data(sheets, worksheet):
    """Test writing data to the sheet."""
    print("✏️  Testing data writing...")
    
    try:
        # Add a test row
        test_row = [
            "TEST",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Integration test",
            "SUCCESS"
        ]
        
        sheets.append_row(worksheet, test_row)
        print("✅ Successfully wrote test data!")
        print(f"   Added row: {test_row}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to write data: {e}")
        print("   Make sure the service account has 'Editor' permissions")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Google Sheets Integration Tests\n")
    
    # Your sheet URL - update this!
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1CwyNMN_YRhU5IaYaG1OXaBGzgoYkBtF5rc9sO9Nyw48/edit"
    
    # Test 1: Authentication
    sheets = test_authentication()
    if not sheets:
        return False
    
    print()
    
    # Test 2: Sheet Access
    spreadsheet, worksheet = test_sheet_access(sheets, SHEET_URL)
    if not worksheet:
        return False
    
    print()
    
    # Test 3: Read Data
    read_success = test_read_data(sheets, worksheet)
    
    print()
    
    # Test 4: Write Data (optional - comment out if you don't want to modify the sheet)
    write_success = test_write_data(sheets, worksheet)
    
    print("\n" + "="*50)
    if read_success and write_success:
        print("🎉 ALL TESTS PASSED!")
        print("Your Google Sheets integration is working perfectly!")
        print("\nNext steps:")
        print("1. Add sheets integration to your IBKR API endpoints")
        print("2. Start logging trades automatically")
        print("3. Set up portfolio tracking")
    else:
        print("⚠️  Some tests failed. Check the messages above.")
    
    return read_success and write_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
