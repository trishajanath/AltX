#!/usr/bin/env python3
"""
Test script to verify AI project assistant functionality
"""

import requests
import json


def test_ai_project_assistant():
    """Test the AI project assistant with Neelesh's personalization request"""
    
    # Test the actual request that was failing
    test_payload = {
        "project_name": "app-1759581989116",  # Use one of the existing projects
        "user_message": "can you include my name which is Neelesh",
        "tech_stack": ["React", "FastAPI", "Vite", "TailwindCSS"],
        "re_run": False
    }
    
    try:
        print("🧪 Testing AI Project Assistant...")
        print(f"Request: {test_payload['user_message']}")
        print(f"Project: {test_payload['project_name']}")
        
        response = requests.post(
            "http://localhost:8000/api/ai-project-assistant",
            json=test_payload,
            timeout=30
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('success', False)}")
            print(f"📝 Explanation: {result.get('explanation', 'No explanation')[:200]}...")
            
            files_modified = result.get('files_modified', [])
            if files_modified:
                print(f"📁 Files Modified: {files_modified}")
            else:
                print("⚠️ No files were modified")
                
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - server might be processing")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - make sure server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_project_list():
    """Check what projects are available"""
    try:
        print("\n📂 Checking available projects...")
        response = requests.get("http://localhost:8000/api/projects", timeout=10)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"Found {len(projects)} projects:")
            for i, project in enumerate(projects[:5]):  # Show first 5
                print(f"  {i+1}. {project.get('name', 'Unknown')}")
        else:
            print(f"Failed to get projects: {response.status_code}")
            
    except Exception as e:
        print(f"Failed to check projects: {e}")


if __name__ == "__main__":
    test_project_list()
    test_ai_project_assistant()