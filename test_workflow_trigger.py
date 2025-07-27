#!/usr/bin/env python3
"""
Test script for GitHub workflow trigger endpoint
"""

import requests
import json

# Test configuration
API_BASE_URL = "http://localhost:8080"  # Adjust port as needed
API_KEY = "test-api-key-123"  # Default API key for testing

def test_workflow_trigger():
    """Test the /trigger-workflow endpoint"""
    
    url = f"{API_BASE_URL}/trigger-workflow"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Test payload
    test_data = {
        "symbol": "AAPL",
        "action": "BUY", 
        "quantity": 1,
        "limit_price": 150.00
    }
    
    print(f"Testing workflow trigger endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=test_data, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Body (raw): {response.text}")
            
        if response.status_code == 200:
            print("✅ Success! Workflow triggered successfully.")
        else:
            print("❌ Failed to trigger workflow.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the Flask server is running.")
    except requests.exceptions.Timeout:
        print("❌ Request timed out.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_workflow_trigger() 