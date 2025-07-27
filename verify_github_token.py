#!/usr/bin/env python3
"""
Simple script to verify your GitHub token is working correctly
Run this before testing the workflow trigger
"""

import requests
import json
import os

def test_github_token():
    """Test if GitHub token can access the repository"""
    
    # Try to get token from config.json first
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            github_config = config.get('github', {})
            token = github_config.get('token', '')
            repo_owner = github_config.get('repo_owner', 'parthchandak02')
            repo_name = github_config.get('repo_name', 'ibkr-ibind-rest-api')
    except FileNotFoundError:
        print("❌ config.json not found!")
        return False
    
    # Fallback to environment variable
    if not token or token == "PASTE_YOUR_GITHUB_TOKEN_HERE":
        token = os.getenv('GITHUB_TOKEN', '')
        if not token:
            print("❌ No GitHub token found!")
            print("Please either:")
            print("1. Add your token to config.json")
            print("2. Set GITHUB_TOKEN environment variable")
            return False
    
    print(f"✅ Found GitHub token")
    print(f"🔍 Testing access to {repo_owner}/{repo_name}...")
    
    # Test repository access
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Successfully accessed repository!")
            print(f"📦 Repository: {repo_data['full_name']}")
            print(f"🔒 Private: {repo_data['private']}")
            return True
        elif response.status_code == 404:
            print("❌ Repository not found or no access!")
            print("Check if:")
            print("1. Repository name is correct")
            print("2. Token has access to this repository")
            return False
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("Check if your token is valid and not expired")
            return False
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 GitHub Token Verification")
    print("=" * 30)
    
    if test_github_token():
        print("\n🎉 Your GitHub token is working correctly!")
        print("You can now test the workflow trigger endpoint.")
    else:
        print("\n❌ GitHub token verification failed.")
        print("Please check your token setup and try again.") 