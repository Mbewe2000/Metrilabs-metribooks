from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from django.utils import timezone

from sales.models import Sale, SaleItem
from inventory.models import Product, ProductCategory, StockMovement
from services.models import Service, ServiceCategory

User = get_user_model()


class SalesAPITestCase(TestCase):
    """Test Sales API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        
        # Set up test data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Set up products and services for testing"""
        # Create inventory category and products
        self.category = ProductCategory.objects.create(
            name=f'electronics-api-{self.user.id}',
            description='Electronic items for API tests'
        )
        
        self.product1 = Product.objects.create(
            user=self.user,
            name='Smartphone',
            description='Latest smartphone',
            category=self.category,
            selling_price=Decimal('800.00'),
            cost_price=Decimal('600.00')
        )
        
        self.product2 = Product.objects.create(
            user=self.user,
            name='Headphones',
            description='Wireless headphones',
            category=self.category,
            selling_price=Decimal('150.00'),
            cost_price=Decimal('100.00')
        )
        
        # Set up inventory for products (signals automatically create inventory)
        from inventory.models import Inventory
        Inventory.objects.filter(product=self.product1).update(quantity_in_stock=Decimal('10.00'))
        Inventory.objects.filter(product=self.product2).update(quantity_in_stock=Decimal('25.00'))
        
        # Refresh products to get updated inventory
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        
        # Create service category and service
        self.service_category = ServiceCategory.objects.create(
            name='IT Services',
            description='Technology services'
        )
        
        self.service = Service.objects.create(
            user=self.user,
            name='Phone Repair',
            description='Smartphone repair service',
            category=self.service_category,
            pricing_type='fixed',
            fixed_price=Decimal('100.00')
        )
    
    def authenticate(self):
        """Authenticate the client"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_create_product_sale_api(self):
        """Test creating a sale with products via API"""
        self.authenticate()
        
        initial_stock = self.product1.current_stock
        
        sale_data = {
            'customer_name': 'John Doe',
            'customer_phone': '+1234567890',
            'payment_method': 'cash',
            'status': 'completed',
            'items': [
                {
                    'item_type': 'product',
                    'product': self.product1.id,
                    'quantity': '2.000',
                    'unit_price': '800.00'
                },
                {
                    'item_type': 'product',
                    'product': self.product2.id,
                    'quantity': '1.000',
                    'unit_price': '150.00'
                }
            ]
        }
        
        response = self.client.post('/api/sales/sales/create/', sale_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check sale was created
        sale = Sale.objects.get(id=response.data['data']['id'])
        self.assertEqual(sale.customer_name, 'John Doe')
        self.assertEqual(sale.payment_method, 'cash')
        self.assertEqual(sale.items.count(), 2)
        
        # Check inventory was updated
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.current_stock, initial_stock - Decimal('2.000'))
        
        # Check inventory movement was created
        movement = StockMovement.objects.filter(
            product=self.product1,
            movement_type='sale'
        ).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, -Decimal('2.000'))  # Negative for outbound
    
    def test_create_service_sale_api(self):
        """Test creating a sale with services via API"""
        self.authenticate()
        
        sale_data = {
            'customer_name': 'Jane Smith',
            'payment_method': 'mobile_money',
            'status': 'completed',
            'items': [
                {
                    'item_type': 'service',
                    'service': self.service.id,
                    'quantity': '1.000',
                    'unit_price': '100.00'
                }
            ]
        }
        
        response = self.client.post('/api/sales/sales/create/', sale_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check sale was created
        sale = Sale.objects.get(id=response.data['data']['id'])
        self.assertEqual(sale.customer_name, 'Jane Smith')
        self.assertEqual(sale.payment_method, 'mobile_money')
        self.assertEqual(sale.items.count(), 1)
        
        # Check sale item
        sale_item = sale.items.first()
        self.assertEqual(sale_item.item_type, 'service')
        self.assertEqual(sale_item.service, self.service)
    
    def test_mixed_product_service_sale_api(self):
        """Test creating a sale with both products and services"""
        self.authenticate()
        
        sale_data = {
            'customer_name': 'Bob Wilson',
            'payment_method': 'card',
            'status': 'completed',
            'items': [
                {
                    'item_type': 'product',
                    'product': self.product1.id,
                    'quantity': '1.000',
                    'unit_price': '800.00'
                },
                {
                    'item_type': 'service',
                    'service': self.service.id,
                    'quantity': '1.000',
                    'unit_price': '100.00'
                }
            ]
        }
        
        response = self.client.post('/api/sales/sales/create/', sale_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check sale was created with both types
        sale = Sale.objects.get(id=response.data['data']['id'])
        self.assertEqual(sale.items.count(), 2)
        
        product_item = sale.items.filter(item_type='product').first()
        service_item = sale.items.filter(item_type='service').first()
        
        self.assertIsNotNone(product_item)
        self.assertIsNotNone(service_item)
        self.assertEqual(product_item.product, self.product1)
        self.assertEqual(service_item.service, self.service)
    
    def test_sale_list_api(self):
        """Test listing sales via API"""
        self.authenticate()
        
        # Create test sales
        sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash',
            customer_name='Customer 1'
        )
        
        sale2 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            payment_method='mobile_money',
            customer_name='Customer 2'
        )
        
        response = self.client.get('/api/sales/sales/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_sale_detail_api(self):
        """Test getting sale details via API"""
        self.authenticate()
        
        sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('150.00'),
            total_amount=Decimal('150.00'),
            payment_method='cash',
            customer_name='Test Customer'
        )
        
        SaleItem.objects.create(
            sale=sale,
            item_type='product',
            product=self.product1,
            item_name=self.product1.name,
            quantity=Decimal('1.000'),
            unit_price=Decimal('150.00'),
            total_price=Decimal('150.00')
        )
        
        response = self.client.get(f'/api/sales/sales/{sale.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_name'], 'Test Customer')
        self.assertEqual(len(response.data['items']), 1)
    
    def test_sale_update_api(self):
        """Test updating a sale via API"""
        self.authenticate()
        
        sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash',
            customer_name='Original Name'
        )
        
        update_data = {
            'customer_name': 'Updated Name',
            'customer_phone': '+9876543210',
            'payment_method': 'mobile_money'
        }
        
        response = self.client.put(f'/api/sales/sales/{sale.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sale.refresh_from_db()
        self.assertEqual(sale.customer_name, 'Updated Name')
        self.assertEqual(sale.customer_phone, '+9876543210')
        self.assertEqual(sale.payment_method, 'mobile_money')
    
    def test_sale_deletion_api(self):
        """Test deleting a sale via API"""
        self.authenticate()
        
        initial_stock = self.product1.current_stock
        
        # Create sale with product
        sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('800.00'),
            total_amount=Decimal('800.00'),
            payment_method='cash',
            status='pending'  # Only pending or cancelled sales can be deleted
        )
        
        SaleItem.objects.create(
            sale=sale,
            item_type='product',
            product=self.product1,
            item_name=self.product1.name,
            quantity=Decimal('1.000'),
            unit_price=Decimal('800.00'),
            total_price=Decimal('800.00')
        )
        
        # Verify stock was reduced
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.current_stock, initial_stock - Decimal('1.000'))
        
        # Delete the sale
        response = self.client.delete(f'/api/sales/sales/{sale.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify sale was deleted
        self.assertFalse(Sale.objects.filter(id=sale.id).exists())
        
        # Verify stock was restored
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.current_stock, initial_stock)
    
    def test_user_isolation_in_sales_api(self):
        """Test that users can only access their own sales"""
        self.authenticate()
        
        # Create sale for user1
        sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash'
        )
        
        # Create sale for user2
        sale2 = Sale.objects.create(
            user=self.user2,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            payment_method='cash'
        )
        
        # User1 should only see their sale
        response = self.client.get('/api/sales/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(sale1.id))
        
        # User1 should not be able to access user2's sale
        response = self.client.get(f'/api/sales/sales/{sale2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access API"""
        # Don't authenticate
        response = self.client.get('/api/sales/sales/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post('/api/sales/sales/create/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_api(self):
        """Test sales dashboard API endpoint"""
        self.authenticate()
        
        # Create some test sales
        Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash',
            sale_date=timezone.now()
        )
        
        Sale.objects.create(
            user=self.user,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            payment_method='mobile_money',
            sale_date=timezone.now()
        )
        
        response = self.client.get('/api/sales/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        dashboard_data = response.data['data']
        self.assertIn('today_sales', dashboard_data)
        self.assertIn('today_revenue', dashboard_data)
        self.assertIn('this_week_sales', dashboard_data)
        self.assertIn('this_week_revenue', dashboard_data)
        self.assertIn('this_month_sales', dashboard_data)
        self.assertIn('this_month_revenue', dashboard_data)
        self.assertIn('recent_sales', dashboard_data)
        self.assertIn('payment_methods', dashboard_data)
        self.assertIn('top_products', dashboard_data)
        self.assertIn('top_services', dashboard_data)
    
    def test_sales_filtering_api(self):
        """Test filtering sales by various parameters"""
        self.authenticate()
        
        from datetime import datetime, timedelta
        
        # Create sales with different dates and payment methods
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash',
            sale_date=datetime.combine(today, datetime.min.time())
        )
        
        sale2 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            payment_method='mobile_money',
            sale_date=datetime.combine(yesterday, datetime.min.time())
        )
        
        # Test date filtering
        response = self.client.get(f'/api/sales/sales/?start_date={today}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test payment method filtering
        response = self.client.get('/api/sales/sales/?payment_method=cash')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test status filtering
        response = self.client.get('/api/sales/sales/?status=completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Both sales should be completed by default
        self.assertEqual(len(response.data), 2)
