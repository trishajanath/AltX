#!/usr/bin/env python3
"""Test the scan endpoint directly"""

import requests
import json

try:
    # Test the scan endpoint
    url = "http://localhost:8000/scan"
    data = {"url": "https://google.com", "model_type": "fast"}
    
    print("🔍 Testing scan endpoint...")
    response = requests.post(url, json=data, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Scan successful! Security Score: {result.get('scan_result', {}).get('security_score', 'N/A')}")
    else:
        print(f"❌ Scan failed: {response.text}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
