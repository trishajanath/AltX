#!/usr/bin/env python3
"""
Simple test for project generation endpoint
"""

import requests
import json

def test_simple_generation():
    """Test the project generation with a simple request"""
    
    url = "http://localhost:8000/generate-project"
    payload = {
        "idea": "Build a simple todo app",
        "project_type": "web-app", 
        "tech_stack": "auto",
        "complexity": "medium"
    }
    
    try:
        print("🧪 Testing project generation...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            
            if data.get('success'):
                project = data.get('project', {})
                print(f"Project Name: {project.get('name')}")
                print(f"Tech Stack: {project.get('tech_stack')}")
                print(f"Features: {len(project.get('features', []))} features")
                print("✅ Project generation successful!")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the backend server is running on http://localhost:8000")

if __name__ == "__main__":
    test_simple_generation()