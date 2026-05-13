#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check UltraMsg instance status
"""

import requests
import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# UltraMsg Configuration
INSTANCE_ID = "26795"
TOKEN = "egswpl1vlle5gjrt"
API_URL = "https://api.ultramsg.com"

def check_instance_status():
    """Check if instance is authenticated and ready"""
    
    url = f"{API_URL}/instance{INSTANCE_ID}/instance/status"
    
    params = {
        'token': TOKEN,
    }
    
    print("=" * 80)
    print(">> Checking UltraMsg Instance Status")
    print("=" * 80)
    print(f"Instance ID: {INSTANCE_ID}")
    print(f"API URL: {url}")
    print("=" * 80)
    print("\n>> Checking...\n")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "=" * 80)
            print(">> INSTANCE STATUS:")
            print("=" * 80)
            
            # Check authentication status
            account_status = data.get('account_status', 'unknown')
            
            if account_status == 'authenticated':
                print(">> Status: CONNECTED")
                print(">> You can send messages!")
                return True
            elif account_status == 'init':
                print(">> Status: INITIALIZING")
                print(">> Scan QR code to authenticate")
                return False
            elif account_status == 'qr':
                print(">> Status: WAITING FOR QR SCAN")
                print(">> Please scan QR code in UltraMsg dashboard")
                return False
            else:
                print(f">> Status: {account_status.upper()}")
                print(">> Check UltraMsg dashboard")
                return False
        else:
            print(f"\n>> HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n>> ERROR: {e}")
        return False

if __name__ == '__main__':
    check_instance_status()

