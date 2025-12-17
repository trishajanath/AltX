"""
Quick test script for MongoDB authentication system
Run this to verify your setup is working correctly
"""
import asyncio
import requests
import json

BASE_URL = "https://api.xverta.com"

def test_signup():
    """Test user signup"""
    print("\n🔵 Testing Signup...")
    
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Signup successful!")
        print(f"   User ID: {result['user']['id']}")
        print(f"   Username: {result['user']['username']}")
        print(f"   Email: {result['user']['email']}")
        print(f"   Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"❌ Signup failed: {response.status_code}")
        print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        return None


def test_login(email="test@example.com", password="TestPass123"):
    """Test user login"""
    print("\n🔵 Testing Login...")
    
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Login successful!")
        print(f"   User ID: {result['user']['id']}")
        print(f"   Username: {result['user']['username']}")
        print(f"   Email: {result['user']['email']}")
        print(f"   Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        return None


def test_get_user(token):
    """Test getting current user info"""
    print("\n🔵 Testing Get Current User...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Get user successful!")
        print(f"   User data: {json.dumps(result['user'], indent=2)}")
        return True
    else:
        print(f"❌ Get user failed: {response.status_code}")
        print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        return False


def test_logout(token):
    """Test logout"""
    print("\n🔵 Testing Logout...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Logout successful!")
        print(f"   Message: {result['message']}")
        return True
    else:
        print(f"❌ Logout failed: {response.status_code}")
        return False


def main():
    """Run all authentication tests"""
    print("=" * 60)
    print("🚀 MongoDB Authentication System - Test Suite")
    print("=" * 60)
    
    # Test 1: Signup
    token = test_signup()
    
    if not token:
        print("\n⚠️  Signup failed, trying login instead...")
        token = test_login()
    
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        print("   Please check:")
        print("   1. Backend is running on port 8000")
        print("   2. MongoDB is configured in .env")
        print("   3. MongoDB connection is working")
        return
    
    # Test 2: Get current user
    test_get_user(token)
    
    # Test 3: Logout
    test_logout(token)
    
    # Test 4: Login again with existing credentials
    token = test_login()
    
    if token:
        test_get_user(token)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("   1. Configure MongoDB URL in backend/.env")
    print("   2. Set JWT_SECRET_KEY in backend/.env")
    print("   3. Access https://xverta.com/auth in your browser")
    print("   4. Create an account and start using the app!")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Backend is not running on https://api.xverta.com")
        print("   Start the backend with: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
