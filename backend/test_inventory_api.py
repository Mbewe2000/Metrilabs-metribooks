"""
Test script for the inventory API endpoints
Run this after starting the Django server and having a valid user token
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

def test_inventory_with_token(access_token):
    """Test inventory endpoints with authentication"""
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 50)
    print("TESTING INVENTORY MODULE")
    print("=" * 50)
    
    # Test 1: Get Categories
    print("\n1. Testing Categories...")
    response = requests.get(f"{BASE_URL}/inventory/categories/", headers=headers)
    print(f"Categories Status: {response.status_code}")
    if response.status_code == 200:
        categories = response.json()
        print(f"Available categories: {len(categories)}")
        if categories:
            print(f"First category: {categories[0]}")
    
    # Test 2: Create a Product
    print("\n2. Testing Product Creation...")
    product_data = {
        "name": "Test Product",
        "sku": "TEST001",
        "description": "A test product for inventory",
        "category": 1,  # Assuming first category exists
        "selling_price": "99.99",
        "cost_price": "70.00",
        "unit_of_measure": "each",
        "opening_stock": "50.000",
        "reorder_level": "10.000",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/inventory/products/create/", 
                           json=product_data, headers=headers)
    print(f"Product Creation Status: {response.status_code}")
    
    product_id = None
    if response.status_code == 201:
        result = response.json()
        print(f"Product created successfully: {result.get('data', {}).get('id')}")
        product_id = result.get('data', {}).get('id')
    else:
        print(f"Error: {response.json()}")
    
    # Test 3: List Products
    print("\n3. Testing Product List...")
    response = requests.get(f"{BASE_URL}/inventory/products/", headers=headers)
    print(f"Product List Status: {response.status_code}")
    if response.status_code == 200:
        products = response.json()
        print(f"Total products: {len(products.get('results', []))}")
    
    # Test 4: Adjust Stock (if product was created)
    if product_id:
        print("\n4. Testing Stock Adjustment...")
        adjustment_data = {
            "adjustment_type": "add",
            "quantity": "25.000",
            "movement_type": "stock_in",
            "reference_number": "REF001",
            "notes": "Test stock addition"
        }
        
        response = requests.post(f"{BASE_URL}/inventory/products/{product_id}/adjust-stock/",
                               json=adjustment_data, headers=headers)
        print(f"Stock Adjustment Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Stock adjusted: {result.get('data')}")
    
    # Test 5: Get Dashboard
    print("\n5. Testing Dashboard...")
    response = requests.get(f"{BASE_URL}/inventory/dashboard/", headers=headers)
    print(f"Dashboard Status: {response.status_code}")
    if response.status_code == 200:
        dashboard = response.json()
        print(f"Dashboard summary: {dashboard.get('data', {}).get('summary')}")
    
    # Test 6: Stock Movements
    print("\n6. Testing Stock Movements...")
    response = requests.get(f"{BASE_URL}/inventory/stock-movements/", headers=headers)
    print(f"Stock Movements Status: {response.status_code}")
    if response.status_code == 200:
        movements = response.json()
        print(f"Total movements: {len(movements.get('results', []))}")
    
    # Test 7: Stock Alerts
    print("\n7. Testing Stock Alerts...")
    response = requests.get(f"{BASE_URL}/inventory/alerts/", headers=headers)
    print(f"Stock Alerts Status: {response.status_code}")
    if response.status_code == 200:
        alerts = response.json()
        print(f"Total alerts: {len(alerts.get('results', []))}")
    
    # Test 8: Reports
    print("\n8. Testing Reports...")
    response = requests.get(f"{BASE_URL}/inventory/reports/stock-summary/", headers=headers)
    print(f"Stock Summary Report Status: {response.status_code}")
    
    response = requests.get(f"{BASE_URL}/inventory/reports/valuation/", headers=headers)
    print(f"Valuation Report Status: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("INVENTORY TESTING COMPLETED")
    print("=" * 50)


def get_auth_token():
    """Get authentication token by logging in"""
    login_data = {
        "email_or_phone": "test@example.com",  # Change to your test user
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        return response.json()['tokens']['access']
    else:
        print("Login failed. Please ensure you have a test user created.")
        print(f"Response: {response.json()}")
        return None


if __name__ == "__main__":
    print("Metrilabs Inventory Module Test Script")
    print("Make sure Django server is running on http://127.0.0.1:8000")
    
    # Get authentication token
    token = get_auth_token()
    
    if token:
        test_inventory_with_token(token)
    else:
        print("Could not obtain authentication token. Please check your credentials.")
