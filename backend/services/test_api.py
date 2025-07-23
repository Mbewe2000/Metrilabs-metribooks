from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date

from .models import ServiceCategory, Service, Worker, ServiceRecord

User = get_user_model()


class ServicesAPITestCase(APITestCase):
    """Test Services API endpoints"""

    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create JWT tokens
        self.token1 = RefreshToken.for_user(self.user1).access_token
        self.token2 = RefreshToken.for_user(self.user2).access_token
        
        # Create API clients
        self.client1 = APIClient()
        self.client1.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        self.client2 = APIClient()
        self.client2.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')
        
        # Get or create a service category
        self.category, _ = ServiceCategory.objects.get_or_create(
            name='beauty_wellness',
            defaults={'description': 'Beauty and wellness services'}
        )

    def test_service_crud_api(self):
        """Test Service CRUD operations via API"""
        
        # Create service via API
        service_data = {
            'name': 'Haircut',
            'description': 'Professional haircut service',
            'category': self.category.id,
            'pricing_type': 'fixed',
            'fixed_price': '50.00'
        }
        
        response = self.client1.post('/api/services/services/create/', service_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response format
        self.assertTrue(response.data['success'])
        service_id = response.data['data']['id']
        
        # List services (should only see user's own services)
        response = self.client1.get('/api/services/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Haircut')
        
        # Other user should not see the service
        response = self.client2.get('/api/services/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
        # Update service
        update_data = {
            'name': 'Premium Haircut',
            'pricing_type': 'fixed',
            'fixed_price': '75.00'
        }
        response = self.client1.patch(f'/api/services/services/{service_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response format (wrapped in success/data)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Premium Haircut')
        
        # Other user should not be able to update
        response = self.client2.patch(f'/api/services/services/{service_id}/', {'name': 'Hack'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Delete service
        response = self.client1.delete(f'/api/services/services/{service_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify deletion
        response = self.client1.get('/api/services/services/')
        self.assertEqual(len(response.data), 0)

    def test_worker_crud_api(self):
        """Test Worker CRUD operations via API"""
        
        # Create worker via API
        worker_data = {
            'name': 'John Doe',
            'employee_id': 'EMP001',
            'phone': '+260771234567',
            'email': 'john@example.com',
            'is_owner': False
        }
        
        response = self.client1.post('/api/services/workers/create/', worker_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response format
        self.assertTrue(response.data['success'])
        worker_id = response.data['data']['id']
        
        # List workers (should include the auto-created owner + new worker)
        response = self.client1.get('/api/services/workers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        
        # Find our created worker
        created_worker = next((w for w in response.data if w['name'] == 'John Doe'), None)
        self.assertIsNotNone(created_worker)
        self.assertEqual(created_worker['employee_id'], 'EMP001')
        
        # Other user should not see the worker
        response = self.client2.get('/api/services/workers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only have the auto-created owner worker
        self.assertEqual(len(response.data), 1)
        self.assertTrue(any(w['is_owner'] for w in response.data))

    def test_service_record_api(self):
        """Test ServiceRecord creation and user isolation"""
        
        # Create service and worker
        service = Service.objects.create(
            user=self.user1,
            name='Haircut',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        worker = Worker.objects.create(
            user=self.user1,
            name='Barber John'
        )
        worker.services.add(service)
        
        # Create service record via API
        record_data = {
            'worker': worker.id,
            'service': service.id,
            'date_performed': str(date.today()),
            'used_fixed_price': True,
            'fixed_price_used': '50.00',
            'customer_name': 'Test Customer',
            'total_amount': '50.00'
        }
        
        response = self.client1.post('/api/services/records/create/', record_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List service records
        response = self.client1.get('/api/services/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['customer_name'], 'Test Customer')
        
        # Other user should not see the record
        response = self.client2.get('/api/services/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_dashboard_api(self):
        """Test dashboard API endpoint"""
        
        # Create some test data
        service = Service.objects.create(
            user=self.user1,
            name='Haircut',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        worker = Worker.objects.create(
            user=self.user1,
            name='Barber John'
        )
        worker.services.add(service)
        
        ServiceRecord.objects.create(
            user=self.user1,
            worker=worker,
            service=service,
            date_performed=date.today(),
            used_fixed_price=True,
            fixed_price_used=Decimal('50.00'),
            total_amount=Decimal('50.00')
        )
        
        # Get dashboard data
        response = self.client1.get('/api/services/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check dashboard structure (wrapped in success/data)
        self.assertTrue(response.data['success'])
        dashboard_data = response.data['data']
        
        self.assertIn('total_services', dashboard_data)
        self.assertIn('total_workers', dashboard_data)
        self.assertIn('today_records', dashboard_data)
        self.assertIn('today_revenue', dashboard_data)
        
        # Check values
        self.assertEqual(dashboard_data['total_services'], 1)
        self.assertGreaterEqual(dashboard_data['total_workers'], 1)  # At least the owner worker
        self.assertEqual(dashboard_data['today_records'], 1)
        self.assertEqual(float(dashboard_data['today_revenue']), 50.00)
        
        # Other user should have different (empty) dashboard
        response = self.client2.get('/api/services/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        dashboard_data2 = response.data['data']
        self.assertEqual(dashboard_data2['today_records'], 0)
        # Handle None values in revenue
        today_revenue2 = dashboard_data2['today_revenue']
        if today_revenue2 is None:
            today_revenue2 = 0
        self.assertEqual(float(today_revenue2), 0.00)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access API"""
        client = APIClient()  # No authentication
        
        endpoints = [
            '/api/services/services/',
            '/api/services/workers/',
            '/api/services/records/',
            '/api/services/dashboard/'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_user_isolation_strict(self):
        """Test strict user isolation - users cannot access each other's data"""
        
        # Create data for user1
        service1 = Service.objects.create(
            user=self.user1,
            name='User1 Service',
            pricing_type='fixed',
            fixed_price=Decimal('50.00')
        )
        
        worker1 = Worker.objects.create(
            user=self.user1,
            name='User1 Worker'
        )
        
        # User2 should not be able to access user1's data by ID
        response = self.client2.get(f'/api/services/services/{service1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = self.client2.get(f'/api/services/workers/{worker1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # User2 should not be able to update user1's data
        response = self.client2.patch(f'/api/services/services/{service1.id}/', {'name': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = self.client2.patch(f'/api/services/workers/{worker1.id}/', {'name': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
