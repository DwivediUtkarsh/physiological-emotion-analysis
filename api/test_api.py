"""
API Endpoint Test Script
Tests all endpoints to ensure they work correctly
"""

import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url, method="GET", params=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        
        success = response.status_code == expected_status
        
        if success:
            data = response.json()
            print(f"✅ {name}")
            return True, data
        else:
            print(f"❌ {name} - Status: {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} - Server not running")
        return False, None
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        return False, None

def main():
    print("\n" + "="*70)
    print("SURJA API ENDPOINT TESTS")
    print("="*70 + "\n")
    
    # Check if server is running
    print("🔍 Checking if API server is running...")
    try:
        response = requests.get(BASE_URL, timeout=2)
        if response.status_code == 200:
            print("✅ API server is running\n")
        else:
            print("❌ API server returned unexpected status\n")
            sys.exit(1)
    except:
        print("❌ API server is NOT running")
        print("Please start the server with: python api/server.py\n")
        sys.exit(1)
    
    results = []
    
    # Health & Status Endpoints
    print("📊 Testing Health & Status Endpoints...")
    results.append(test_endpoint(
        "GET /", 
        f"{BASE_URL}/"
    ))
    results.append(test_endpoint(
        "GET /api/health", 
        f"{BASE_URL}/api/health"
    ))
    results.append(test_endpoint(
        "GET /api/stats", 
        f"{BASE_URL}/api/stats"
    ))
    print()
    
    # Prediction Endpoints
    print("🎯 Testing Prediction Endpoints...")
    results.append(test_endpoint(
        "GET /api/predictions/active", 
        f"{BASE_URL}/api/predictions/active"
    ))
    results.append(test_endpoint(
        "GET /api/predictions/active?video_id=2", 
        f"{BASE_URL}/api/predictions/active",
        params={'video_id': 2}
    ))
    results.append(test_endpoint(
        "GET /api/predictions/all", 
        f"{BASE_URL}/api/predictions/all"
    ))
    results.append(test_endpoint(
        "GET /api/predictions/all?limit=10", 
        f"{BASE_URL}/api/predictions/all",
        params={'limit': 10}
    ))
    results.append(test_endpoint(
        "GET /api/predictions/timeline?video_id=2", 
        f"{BASE_URL}/api/predictions/timeline",
        params={'video_id': 2}
    ))
    print()
    
    # Emotion Endpoints
    print("😊 Testing Emotion Endpoints...")
    results.append(test_endpoint(
        "GET /api/emotions/current", 
        f"{BASE_URL}/api/emotions/current"
    ))
    results.append(test_endpoint(
        "GET /api/emotions/history", 
        f"{BASE_URL}/api/emotions/history"
    ))
    results.append(test_endpoint(
        "GET /api/emotions/history?limit=10", 
        f"{BASE_URL}/api/emotions/history",
        params={'limit': 10}
    ))
    results.append(test_endpoint(
        "GET /api/emotions/video/2", 
        f"{BASE_URL}/api/emotions/video/2"
    ))
    print()
    
    # Signal Endpoints
    print("📡 Testing Signal Endpoints...")
    results.append(test_endpoint(
        "GET /api/signals/latest", 
        f"{BASE_URL}/api/signals/latest"
    ))
    results.append(test_endpoint(
        "GET /api/signals/latest?count=20", 
        f"{BASE_URL}/api/signals/latest",
        params={'count': 20}
    ))
    results.append(test_endpoint(
        "GET /api/signals/stats", 
        f"{BASE_URL}/api/signals/stats"
    ))
    print()
    
    # Video Endpoints
    print("🎬 Testing Video Endpoints...")
    results.append(test_endpoint(
        "GET /api/videos/current", 
        f"{BASE_URL}/api/videos/current"
    ))
    results.append(test_endpoint(
        "GET /api/videos/history", 
        f"{BASE_URL}/api/videos/history"
    ))
    print()
    
    # Session Endpoints
    print("📈 Testing Session Endpoints...")
    results.append(test_endpoint(
        "GET /api/session/summary", 
        f"{BASE_URL}/api/session/summary"
    ))
    results.append(test_endpoint(
        "GET /api/session/emotion-timeline", 
        f"{BASE_URL}/api/session/emotion-timeline"
    ))
    print()
    
    # Test error handling
    print("⚠️  Testing Error Handling...")
    results.append(test_endpoint(
        "GET /api/notfound (404)", 
        f"{BASE_URL}/api/notfound",
        expected_status=404
    ))
    print()
    
    # Summary
    passed = sum(1 for r in results if r[0])
    total = len(results)
    
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    print("\n" + "="*70 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

