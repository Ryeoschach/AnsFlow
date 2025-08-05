#!/usr/bin/env python3
"""
Test script for Settings Management API endpoints.
Tests all the high-priority API functionality.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
SETTINGS_URL = f"{BASE_URL}/settings"

def test_endpoint(url, method="GET", data=None, description=""):
    """Test an API endpoint and return the result."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            json_response = response.json()
            print(f"Response: {json.dumps(json_response, indent=2)}")
            return json_response
        except json.JSONDecodeError:
            print(f"Response (text): {response.text}")
            return response.text
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Django server is not running")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Run all Settings Management API tests."""
    print("🧪 Testing Settings Management API endpoints")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Health check
    test_endpoint(f"{BASE_URL}/health/", description="Health Check")
    
    # Test 2: Users Management
    print("\n" + "🔷" * 20 + " USER MANAGEMENT " + "🔷" * 20)
    
    # List users
    users_response = test_endpoint(f"{SETTINGS_URL}/users/", description="List Users")
    
    # Create test user
    test_user_data = {
        "username": "test_settings_user",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True
    }
    created_user = test_endpoint(
        f"{SETTINGS_URL}/users/", 
        method="POST", 
        data=test_user_data,
        description="Create Test User"
    )
    
    # Test 3: Audit Logs
    print("\n" + "🔷" * 20 + " AUDIT LOGS " + "🔷" * 20)
    
    # List audit logs
    test_endpoint(f"{SETTINGS_URL}/audit-logs/", description="List Audit Logs")
    
    # Create audit log
    audit_log_data = {
        "action": "test_action",
        "object_type": "test_object",
        "object_id": "123",
        "changes": {"test": "data"},
        "ip_address": "127.0.0.1",
        "user_agent": "Test Agent"
    }
    test_endpoint(
        f"{SETTINGS_URL}/audit-logs/", 
        method="POST", 
        data=audit_log_data,
        description="Create Audit Log"
    )
    
    # Test 4: System Alerts
    print("\n" + "🔷" * 20 + " SYSTEM ALERTS " + "🔷" * 20)
    
    # List system alerts
    test_endpoint(f"{SETTINGS_URL}/system-alerts/", description="List System Alerts")
    
    # Create system alert
    alert_data = {
        "level": "warning",
        "title": "Test Alert",
        "message": "This is a test system alert",
        "source": "api_test"
    }
    test_endpoint(
        f"{SETTINGS_URL}/system-alerts/", 
        method="POST", 
        data=alert_data,
        description="Create System Alert"
    )
    
    # Test 5: Notification Configs
    print("\n" + "🔷" * 20 + " NOTIFICATION CONFIGS " + "🔷" * 20)
    
    # List notification configs
    test_endpoint(f"{SETTINGS_URL}/notification-configs/", description="List Notification Configs")
    
    # Create notification config
    notification_data = {
        "type": "email",
        "enabled": True,
        "config": {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "use_tls": True
        }
    }
    test_endpoint(
        f"{SETTINGS_URL}/notification-configs/", 
        method="POST", 
        data=notification_data,
        description="Create Notification Config"
    )
    
    # Test 6: Global Configs
    print("\n" + "🔷" * 20 + " GLOBAL CONFIGS " + "🔷" * 20)
    
    # List global configs
    test_endpoint(f"{SETTINGS_URL}/global-configs/", description="List Global Configs")
    
    # Create global config
    global_config_data = {
        "key": "test_setting",
        "value": "test_value",
        "description": "Test configuration setting"
    }
    test_endpoint(
        f"{SETTINGS_URL}/global-configs/", 
        method="POST", 
        data=global_config_data,
        description="Create Global Config"
    )
    
    # Test 7: Backup Records
    print("\n" + "🔷" * 20 + " BACKUP RECORDS " + "🔷" * 20)
    
    # List backup records
    test_endpoint(f"{SETTINGS_URL}/backup-records/", description="List Backup Records")
    
    # Create backup record
    backup_data = {
        "type": "database",
        "status": "completed",
        "file_path": "/backups/test_backup.sql",
        "file_size": 1024000,
        "metadata": {"tables": 10, "records": 1000}
    }
    test_endpoint(
        f"{SETTINGS_URL}/backup-records/", 
        method="POST", 
        data=backup_data,
        description="Create Backup Record"
    )
    
    # Test 8: System Monitoring
    print("\n" + "🔷" * 20 + " SYSTEM MONITORING " + "🔷" * 20)
    
    # Get system statistics
    test_endpoint(f"{SETTINGS_URL}/system-stats/", description="Get System Statistics")
    
    # Get system health
    test_endpoint(f"{SETTINGS_URL}/system-health/", description="Get System Health")
    
    print("\n" + "🎉" * 20 + " TESTS COMPLETED " + "🎉" * 20)
    print("Settings Management API testing completed!")

if __name__ == "__main__":
    main()
