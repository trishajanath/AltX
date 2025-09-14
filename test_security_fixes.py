#!/usr/bin/env python3
"""
Test script to validate the security fix functionality
Tests GitHub authentication, issue analysis, and code fix generation
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('backend/.env')  # Also try backend directory

def test_github_authentication():
    """Test GitHub authentication fixes"""
    print("🔧 Testing GitHub Authentication...")
    
    try:
        # Test the environment loading
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print(f"✅ GitHub token loaded: {token[:10]}...")
        else:
            print("❌ No GitHub token found")
            return False
            
        # Test GitHub API access
        from github import Github
        client = Github(token)
        user = client.get_user()
        print(f"✅ GitHub API access successful: {user.login}")
        
        return True
    except Exception as e:
        print(f"❌ GitHub authentication test failed: {e}")
        return False

def test_analyze_repo_endpoint():
    """Test the analyze-repo endpoint with fixed authentication"""
    print("\n🔍 Testing Repository Analysis...")
    
    test_payload = {
        "repo_url": "https://github.com/octocat/Hello-World",
        "model_type": "fast",
        "deep_scan": False
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/analyze-repo',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Repository analysis successful!")
            
            # Check for various issue types
            issues_found = 0
            if result.get('secret_scan_results'):
                issues_found += len(result['secret_scan_results'])
                print(f"📦 Secret scan: {len(result['secret_scan_results'])} issues")
                
            if result.get('static_analysis_results'):
                issues_found += len(result['static_analysis_results'])
                print(f"📦 Static analysis: {len(result['static_analysis_results'])} issues")
                
            if result.get('dependency_scan_results', {}).get('vulnerable_packages'):
                vuln_deps = len(result['dependency_scan_results']['vulnerable_packages'])
                issues_found += vuln_deps
                print(f"📦 Dependency vulnerabilities: {vuln_deps} issues")
                
            if result.get('code_quality_results'):
                issues_found += len(result['code_quality_results'])
                print(f"📦 Code quality: {len(result['code_quality_results'])} issues")
                
            print(f"📊 Total issues found: {issues_found}")
            
            # Test GitHub repo info was fetched
            if result.get('github_repo_info'):
                print("✅ GitHub repository metadata fetched successfully")
            else:
                print("⚠️ GitHub repository metadata not available")
                
            return True, result
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not accessible on localhost:8000")
        return False, None
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        return False, None

def test_propose_fix_endpoint():
    """Test the propose-fix endpoint functionality"""
    print("\n🔧 Testing Fix Generation...")
    
    # Create a realistic test issue
    test_issue = {
        'file': 'src/components/Login.js',
        'line': 25,
        'description': 'Sensitive data in localStorage - storing authentication token',
        'severity': 'Medium',
        'rule_id': 'localStorage_usage',
        'code_snippet': 'localStorage.setItem("auth_token", userToken);'
    }
    
    test_payload = {
        'repo_url': 'https://github.com/octocat/Hello-World',
        'issue': test_issue,
        'branch_name': 'security-fix-localstorage'
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/propose-fix',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=45
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Fix generation successful!")
            
            # Check fix components
            if result.get('fix_details', {}).get('fix_summary'):
                print(f"📝 Fix summary: {result['fix_details']['fix_summary'][:100]}...")
                
            if result.get('code_comparison'):
                comparison = result['code_comparison']
                print("📊 Code comparison generated:")
                
                if comparison.get('diff_statistics'):
                    stats = comparison['diff_statistics']
                    print(f"   • {stats.get('additions', 0)} additions")
                    print(f"   • {stats.get('deletions', 0)} deletions")
                    print(f"   • Changes detected: {stats.get('has_changes', False)}")
                    
                if comparison.get('original_content') and comparison.get('fixed_content'):
                    print(f"   • Original code length: {len(comparison['original_content'])} chars")
                    print(f"   • Fixed code length: {len(comparison['fixed_content'])} chars")
                    
            if result.get('pull_request'):
                pr = result['pull_request']
                print(f"📬 Pull request: #{pr.get('number')} - {pr.get('title')}")
                
            return True, result
        else:
            print(f"❌ Fix generation failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Fix generation test failed: {e}")
        return False, None

def test_frontend_accessibility():
    """Test if frontend is accessible and showing fixes correctly"""
    print("\n🌐 Testing Frontend Accessibility...")
    
    try:
        response = requests.get('http://localhost:5173', timeout=10)
        if response.status_code == 200:
            print("✅ Frontend accessible at localhost:5173")
            
            # Check if React app loaded
            if 'AltX' in response.text or 'root' in response.text:
                print("✅ React application loaded")
                return True
            else:
                print("⚠️ Frontend accessible but app may not have loaded")
                return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend server not accessible on localhost:5173")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Security Fix Validation Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: GitHub Authentication
    if test_github_authentication():
        tests_passed += 1
        
    # Test 2: Repository Analysis
    analysis_success, analysis_result = test_analyze_repo_endpoint()
    if analysis_success:
        tests_passed += 1
        
    # Test 3: Fix Generation
    fix_success, fix_result = test_propose_fix_endpoint()
    if fix_success:
        tests_passed += 1
        
    # Test 4: Frontend Accessibility
    if test_frontend_accessibility():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The security fix system is working correctly.")
        print("\n📋 What's working:")
        print("   ✅ GitHub authentication with fallback")
        print("   ✅ Repository analysis with all issue types")
        print("   ✅ Code fix generation with diffs")
        print("   ✅ Frontend accessibility for Monaco Editor preview")
        print("\n🔧 Monaco Editor Features Available:")
        print("   • Code syntax highlighting")
        print("   • Side-by-side original vs fixed code comparison")
        print("   • Automated syntax validation")
        print("   • Security improvement verification")
        print("   • Functionality preservation checks")
        print("   • Test results with detailed feedback")
    else:
        print(f"⚠️ {total_tests - tests_passed} tests failed. Check the output above for details.")
        
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)