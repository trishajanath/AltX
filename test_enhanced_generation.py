#!/usr/bin/env python3
"""
Test script for the enhanced project generation system
"""

import requests
import json
import time

def test_project_generation():
    """Test the full-stack project generation"""
    
    # Test data
    test_ideas = [
        {
            "idea": "Build a todo list app with AI reminders",
            "expected_features": ["AI Integration", "Database Storage"]
        },
        {
            "idea": "Create a blog with user authentication",
            "expected_features": ["User Authentication", "Database Storage"]
        },
        {
            "idea": "Make a simple landing page for my business",
            "expected_features": ["Responsive Design"]
        }
    ]
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Enhanced Project Generation System")
    print("=" * 50)
    
    for i, test_case in enumerate(test_ideas, 1):
        print(f"\n📝 Test {i}: {test_case['idea']}")
        print("-" * 30)
        
        # Make request to generate project
        payload = {
            "idea": test_case["idea"],
            "project_type": "web-app",
            "tech_stack": "auto",
            "complexity": "medium"
        }
        
        try:
            response = requests.post(f"{base_url}/generate-project", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    project = data["project"]
                    print(f"✅ Project Generated: {project['name']}")
                    print(f"📦 Tech Stack: {', '.join(project['tech_stack'])}")
                    print(f"⏱️  Estimated Time: {project['estimated_time']}")
                    print(f"🎯 Features: {len(project['features'])} features")
                    
                    # Check if expected features are present
                    for expected_feature in test_case["expected_features"]:
                        if expected_feature in project["features"]:
                            print(f"   ✅ {expected_feature}")
                        else:
                            print(f"   ❌ Missing: {expected_feature}")
                    
                    # Test file tree endpoint
                    project_name = project["name"].lower().replace(" ", "-")
                    tree_response = requests.get(f"{base_url}/project-file-tree?project_name={project_name}")
                    
                    if tree_response.status_code == 200:
                        tree_data = tree_response.json()
                        if tree_data.get("success"):
                            print(f"📁 File Tree: {len(tree_data.get('tree', []))} items")
                        else:
                            print(f"❌ File Tree Error: {tree_data.get('error')}")
                    
                else:
                    print(f"❌ Generation Failed: {data.get('error')}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
            print("💡 Make sure the backend server is running on http://localhost:8000")
            break
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("🏁 Testing Complete!")

if __name__ == "__main__":
    test_project_generation()