#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test WhatsApp sending via UltraMsg API
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

# Test phone numbers - try different formats
PHONE_FORMATS = [
    "9647800114976",           # Without +
    "+9647800114976",          # With +
    "9647800114976@c.us",      # WhatsApp format
]

# Test with FIRST number
PHONE = PHONE_FORMATS[0]

# Test message
MESSAGE = """مرحباً! 

هذه رسالة تجريبية من نظام Lugal-AI

رقم الطلب: TEST-001
المجموع: $100.00
المجموع بالدينار: 147,000 د.ع

النظام يعمل بنجاح!

شكراً لك"""

def send_whatsapp_text(phone_format):
    """Send text message via UltraMsg"""
    
    url = f"{API_URL}/instance{INSTANCE_ID}/messages/chat"
    
    data = {
        'token': TOKEN,
        'to': phone_format,
        'body': MESSAGE,
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print("=" * 80)
    print(">> Testing WhatsApp Send via UltraMsg")
    print("=" * 80)
    print(f"Phone: {phone_format}")
    print(f"API URL: {url}")
    print(f"Token: {TOKEN[:10]}...")
    print("=" * 80)
    print("\n>> Sending...\n")
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('sent') == 'true':
                print("\n>> SUCCESS! Message sent successfully!")
                return True
            else:
                print(f"\n>> FAILED! Error: {response_data.get('error')}")
                return False
        else:
            print(f"\n>> HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n>> ERROR: Request timeout")
        return False
    except Exception as e:
        print(f"\n>> ERROR: {e}")
        return False

if __name__ == '__main__':
    print("\n>> Testing different phone formats...\n")
    
    for i, phone in enumerate(PHONE_FORMATS, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(PHONE_FORMATS)}: {phone}")
        print(f"{'='*80}\n")
        
        result = send_whatsapp_text(phone)
        
        if result:
            print(f"\n>> Format '{phone}' WORKS!")
            break
        else:
            print(f"\n>> Format '{phone}' failed, trying next...\n")
    
    print("\n" + "="*80)
    print(">> Testing completed!")
    print("="*80)


