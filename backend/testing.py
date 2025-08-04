import requests
import json

BASE_URL = "http://localhost:8000"

def test_rag_integration():
    """Test the complete RAG integration"""
    
    print("🧪 Testing RAG System Integration")
    print("=" * 50)
    
    # Test 1: RAG Query System
    print("\n1️⃣ Testing RAG Query System...")
    try:
        from rag_query import get_secure_coding_patterns
        result = get_secure_coding_patterns("SQL injection prevention")
        print(f"✅ RAG Query works: {len(result)} characters returned")
    except Exception as e:
        print(f"❌ RAG Query failed: {e}")
    
    # Test 2: AI Chat with RAG
    print("\n2️⃣ Testing AI Chat with RAG...")
    try:
        response = requests.post(f"{BASE_URL}/ai-chat", json={
            "question": "What is XSS and how do I prevent it?",
            "context": "general",
            "model_type": "fast"
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('rag_enhanced'):
                print("✅ AI Chat with RAG enhancement works")
            else:
                print("⚠️ AI Chat works but RAG enhancement not detected")
        else:
            print(f"❌ AI Chat failed: {response.status_code}")
    except Exception as e:
        print(f"❌ AI Chat test failed: {e}")
    
    # Test 3: Propose Fix Endpoint
    print("\n3️⃣ Testing Propose Fix Endpoint...")
    try:
        # This would need a real repo to test fully
        test_data = {
            "repo_url": "https://github.com/test/repo",
            "issue": {
                "file": "app.py",
                "line": 10,
                "type": "Static Analysis",
                "description": "Use of eval() can lead to code injection",
                "vulnerable_code": "result = eval(user_input)"
            }
        }
        
        response = requests.post(f"{BASE_URL}/propose-fix", json=test_data)
        print(f"📡 Propose Fix endpoint exists: {response.status_code}")
        # Note: This will likely fail without a real repo, but at least we know the endpoint exists
        
    except Exception as e:
        print(f"ℹ️ Propose Fix test: {e}")
    
    print("\n✅ RAG Integration Test Complete!")

if __name__ == "__main__":
    test_rag_integration()