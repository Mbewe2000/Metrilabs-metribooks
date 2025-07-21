"""
Test script for the authentication API endpoints
Run this after starting the Django server
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api/auth"

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    data = {
        "email": "test@example.com",
        "phone": "+1234567890",
        "password": "testpassword123",
        "password_confirm": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=data)
    print(f"Registration Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        return response.json()['tokens']
    return None

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    data = {
        "email_or_phone": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/login/", json=data)
    print(f"Login Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json()['tokens']
    return None

def test_profile(access_token):
    """Test getting user profile"""
    print("\nTesting user profile...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    
    print(f"Profile Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_change_password(access_token):
    """Test changing password"""
    print("\nTesting password change...")
    
    data = {
        "old_password": "testpassword123",
        "new_password": "newpassword123",
        "new_password_confirm": "newpassword123"
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(f"{BASE_URL}/change-password/", json=data, headers=headers)
    
    print(f"Change Password Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_reset_password():
    """Test password reset request"""
    print("\nTesting password reset...")
    
    data = {
        "email_or_phone": "test@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/reset-password/", json=data)
    print(f"Reset Password Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_logout(refresh_token, access_token):
    """Test user logout"""
    print("\nTesting user logout...")
    
    data = {
        "refresh_token": refresh_token
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/logout/", json=data, headers=headers)
    
    print(f"Logout Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("=== Authentication API Test ===")
    
    # Test registration
    tokens = test_registration()
    
    if tokens:
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        # Test profile access
        test_profile(access_token)
        
        # Test password change
        test_change_password(access_token)
        
        # Test password reset
        test_reset_password()
        
        # Test logout
        test_logout(refresh_token, access_token)
    else:
        # If registration fails, try login
        tokens = test_login()
        if tokens:
            access_token = tokens['access']
            test_profile(access_token)
    
    print("\n=== Test completed ===")
