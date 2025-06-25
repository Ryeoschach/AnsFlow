#!/usr/bin/env python3
"""
Test script for AnsFlow Django API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_authentication():
    """Test JWT authentication"""
    print("Testing authentication...")
    
    # Try to get token
    auth_data = {
        "username": "admin",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json=auth_data)
    print(f"Auth Status: {response.status_code}")
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"Access Token: {tokens['access'][:50]}...")
        return tokens['access']
    else:
        print(f"Auth failed: {response.text}")
        return None

def test_projects_api(token=None):
    """Test projects API"""
    print("Testing projects API...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    response = requests.get(f"{BASE_URL}/api/v1/projects/projects/", headers=headers)
    print(f"Projects Status: {response.status_code}")
    
    if response.status_code == 200:
        projects = response.json()
        print(f"Found {len(projects['results']) if 'results' in projects else len(projects)} projects")
        if projects:
            first_project = projects['results'][0] if 'results' in projects else projects[0]
            print(f"First project: {first_project.get('name', 'N/A')}")
    else:
        print(f"Projects API failed: {response.text}")
    print("-" * 50)

def test_pipelines_api(token=None):
    """Test pipelines API"""
    print("Testing pipelines API...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    response = requests.get(f"{BASE_URL}/api/v1/pipelines/pipelines/", headers=headers)
    print(f"Pipelines Status: {response.status_code}")
    
    if response.status_code == 200:
        pipelines = response.json()
        print(f"Found {len(pipelines['results']) if 'results' in pipelines else len(pipelines)} pipelines")
        if pipelines:
            first_pipeline = pipelines['results'][0] if 'results' in pipelines else pipelines[0]
            print(f"First pipeline: {first_pipeline.get('name', 'N/A')}")
    else:
        print(f"Pipelines API failed: {response.text}")
    print("-" * 50)

def main():
    print("=" * 60)
    print("AnsFlow Django API Test")
    print("=" * 60)
    
    # Test health check
    test_health_check()
    
    # Test authentication
    token = test_authentication()
    
    # Test API endpoints
    test_projects_api(token)
    test_pipelines_api(token)
    
    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()
