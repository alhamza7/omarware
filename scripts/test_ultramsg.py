#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test ULTRAMSG API directly"""

import requests
import json

# Configuration
INSTANCE_ID = "26795"
API_TOKEN = "egswpl1vlle5gjrt"
API_URL = "https://api.ultramsg.com"
PHONE = "9647800114976"  # Already formatted with 964

# Test sending text message
def test_send_text():
    url = f"{API_URL}/{INSTANCE_ID}/messages/chat"
    data = {
        'token': API_TOKEN,
        'to': PHONE,
        'body': 'Test message from Python Script'
    }
    
    print(f"Testing ULTRAMSG API...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('sent') == 'true':
            print("\n✓ SUCCESS! Message sent successfully!")
            return True
        else:
            print(f"\n✗ FAILED! Error: {response_data.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ TIMEOUT! API did not respond")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n✗ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("ULTRAMSG API Direct Test")
    print("=" * 50)
    test_send_text()

