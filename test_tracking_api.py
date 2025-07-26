#!/usr/bin/env python3
"""
Test script for Hayago Mapping Tracking API
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:5000/api"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_location_update():
    """Test location update endpoint"""
    print("\nTesting location update...")
    
    location_data = {
        "driver_id": "test_driver_001",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "speed": 25.5,
        "heading": 180.0,
        "accuracy": 5.0,
        "is_offline": False,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/location",
            json=location_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Location update successful: {data}")
            return True
        else:
            print(f"✗ Location update failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Location update failed: {e}")
        return False

def test_batch_location_update():
    """Test batch location update endpoint"""
    print("\nTesting batch location update...")
    
    batch_data = {
        "locations": [
            {
                "driver_id": "test_driver_002",
                "latitude": 37.7849,
                "longitude": -122.4094,
                "speed": 30.0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            {
                "driver_id": "test_driver_002",
                "latitude": 37.7859,
                "longitude": -122.4084,
                "speed": 32.0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/location/batch",
            json=batch_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Batch location update successful: {data}")
            return True
        else:
            print(f"✗ Batch location update failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Batch location update failed: {e}")
        return False

def test_get_driver_locations():
    """Test get driver locations endpoint"""
    print("\nTesting get driver locations...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/location/test_driver_001?hours=1&limit=10",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Get driver locations successful: Found {data.get('count', 0)} locations")
            return True
        else:
            print(f"✗ Get driver locations failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Get driver locations failed: {e}")
        return False

def test_get_latest_location():
    """Test get latest location endpoint"""
    print("\nTesting get latest location...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/location/test_driver_001/latest",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Get latest location successful: {data}")
            return True
        elif response.status_code == 404:
            print("✓ Get latest location returned 404 (no data found) - this is expected for new driver")
            return True
        else:
            print(f"✗ Get latest location failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Get latest location failed: {e}")
        return False

def test_sync_status():
    """Test sync status endpoint"""
    print("\nTesting sync status...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/sync/status",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sync status successful: {data}")
            return True
        else:
            print(f"✗ Sync status failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Sync status failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Hayago Mapping Tracking API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_location_update,
        test_batch_location_update,
        test_get_driver_locations,
        test_get_latest_location,
        test_sync_status
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

