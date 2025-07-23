from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from inventory.models import Product, ProductCategory, Inventory, StockMovement, StockAlert

User = get_user_model()


class InventoryAPITestCase(APITestCase):
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
        
        # Create test categories
        self.category1, created = ProductCategory.objects.get_or_create(
            name='electronics',
            defaults={'description': 'Electronic products'}
        )
        self.category2, created = ProductCategory.objects.get_or_create(
            name='food_beverage',
            defaults={'description': 'Food and beverage products'}
        )
        
        # Create authentication tokens
        self.token1 = RefreshToken.for_user(self.user1).access_token
        self.token2 = RefreshToken.for_user(self.user2).access_token
        
        # Set up API client
        self.client = APIClient()
    
    def authenticate_user1(self):
        """Authenticate as user1"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
    
    def authenticate_user2(self):
        """Authenticate as user2"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')


class ProductAPITest(InventoryAPITestCase):
    
    def test_create_product(self):
        """Test creating a new product"""
        self.authenticate_user1()
        
        data = {
            'name': 'Test Laptop',
            'sku': 'LAP001',
            'description': 'A test laptop',
            'category': self.category1.id,
            'selling_price': '999.99',
            'cost_price': '700.00',
            'unit_of_measure': 'each',
            'opening_stock': '10.000',
            'reorder_level': '5.000',
            'is_active': True
        }
        
        url = reverse('inventory:product-create')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify product was created
        product = Product.objects.get(name='Test Laptop', user=self.user1)
        self.assertEqual(product.user, self.user1)
        self.assertEqual(product.sku, 'LAP001')
        
        # Verify inventory was created
        inventory = Inventory.objects.get(product=product)
        self.assertEqual(inventory.quantity_in_stock, Decimal('10.000'))
        self.assertEqual(inventory.reorder_level, Decimal('5.000'))
    
    def test_list_products_user_isolation(self):
        """Test that users only see their own products"""
        # Create products for each user
        Product.objects.create(
            user=self.user1,
            name='User1 Product',
            selling_price=Decimal('100.00'),
            category=self.category1
        )
        Product.objects.create(
            user=self.user2,
            name='User2 Product',
            selling_price=Decimal('200.00'),
            category=self.category1
        )
        
        # Test user1 can only see their product
        self.authenticate_user1()
        url = reverse('inventory:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'User1 Product')
        
        # Test user2 can only see their product
        self.authenticate_user2()
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'User2 Product')
    
    def test_update_product(self):
        """Test updating a product"""
        product = Product.objects.create(
            user=self.user1,
            name='Original Name',
            selling_price=Decimal('100.00'),
            category=self.category1
        )
        
        self.authenticate_user1()
        
        data = {
            'name': 'Updated Name',
            'selling_price': '150.00'
        }
        
        url = reverse('inventory:product-detail', kwargs={'pk': product.id})
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify update
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated Name')
        self.assertEqual(product.selling_price, Decimal('150.00'))
    
    def test_delete_product_user_isolation(self):
        """Test that users can only delete their own products"""
        product1 = Product.objects.create(
            user=self.user1,
            name='User1 Product',
            selling_price=Decimal('100.00'),
            category=self.category1
        )
        product2 = Product.objects.create(
            user=self.user2,
            name='User2 Product',
            selling_price=Decimal('200.00'),
            category=self.category1
        )
        
        # User1 tries to delete user2's product (should fail)
        self.authenticate_user1()
        url = reverse('inventory:product-detail', kwargs={'pk': product2.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Product.objects.filter(id=product2.id).exists())
        
        # User1 deletes their own product (should succeed)
        url = reverse('inventory:product-detail', kwargs={'pk': product1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(Product.objects.filter(id=product1.id).exists())


class StockAdjustmentAPITest(InventoryAPITestCase):
    
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            user=self.user1,
            name='Test Product',
            selling_price=Decimal('100.00')
        )
        # Set initial stock
        self.product.inventory.quantity_in_stock = Decimal('50.000')
        self.product.inventory.save()
    
    def test_stock_adjustment_add(self):
        """Test adding stock"""
        self.authenticate_user1()
        
        data = {
            'adjustment_type': 'add',
            'quantity': '25.000',
            'movement_type': 'stock_in',
            'reference_number': 'REF001',
            'notes': 'Test stock addition'
        }
        
        url = reverse('inventory:stock-adjustment', kwargs={'product_id': self.product.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify stock was added
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.quantity_in_stock, Decimal('75.000'))
        
        # Verify stock movement was created
        movement = StockMovement.objects.filter(product=self.product).first()
        self.assertEqual(movement.quantity, Decimal('25.000'))
        self.assertEqual(movement.movement_type, 'stock_in')
        self.assertEqual(movement.created_by, self.user1)
    
    def test_stock_adjustment_remove(self):
        """Test removing stock"""
        self.authenticate_user1()
        
        data = {
            'adjustment_type': 'remove',
            'quantity': '15.000',
            'movement_type': 'stock_out',
            'notes': 'Test stock removal'
        }
        
        url = reverse('inventory:stock-adjustment', kwargs={'product_id': self.product.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify stock was removed
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.quantity_in_stock, Decimal('35.000'))
    
    def test_stock_adjustment_insufficient_stock(self):
        """Test removing more stock than available"""
        self.authenticate_user1()
        
        data = {
            'adjustment_type': 'remove',
            'quantity': '100.000',  # More than available (50)
            'movement_type': 'stock_out'
        }
        
        url = reverse('inventory:stock-adjustment', kwargs={'product_id': self.product.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
        # Verify stock wasn't changed
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.quantity_in_stock, Decimal('50.000'))


class DashboardAPITest(InventoryAPITestCase):
    
    def setUp(self):
        super().setUp()
        # Create some test products for user1
        self.product1 = Product.objects.create(
            user=self.user1,
            name='Product 1',
            selling_price=Decimal('100.00'),
            cost_price=Decimal('70.00')
        )
        self.product2 = Product.objects.create(
            user=self.user1,
            name='Product 2',
            selling_price=Decimal('200.00'),
            cost_price=Decimal('150.00')
        )
        
        # Set stock levels
        self.product1.inventory.quantity_in_stock = Decimal('100.000')
        self.product1.inventory.reorder_level = Decimal('20.000')
        self.product1.inventory.save()
        
        self.product2.inventory.quantity_in_stock = Decimal('5.000')  # Low stock
        self.product2.inventory.reorder_level = Decimal('10.000')
        self.product2.inventory.save()
    
    def test_dashboard_data(self):
        """Test dashboard API returns correct data"""
        self.authenticate_user1()
        
        url = reverse('inventory:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        summary = response.data['data']['summary']
        self.assertEqual(summary['total_products'], 2)
        self.assertEqual(summary['low_stock_count'], 1)  # Product 2 is low stock
        self.assertEqual(summary['out_of_stock_count'], 0)
        
        # Check inventory values
        expected_cost_value = (Decimal('100.000') * Decimal('70.00')) + (Decimal('5.000') * Decimal('150.00'))
        expected_selling_value = (Decimal('100.000') * Decimal('100.00')) + (Decimal('5.000') * Decimal('200.00'))
        
        self.assertEqual(Decimal(str(summary['total_cost_value'])), expected_cost_value)
        self.assertEqual(Decimal(str(summary['total_selling_value'])), expected_selling_value)


class CategoryAPITest(InventoryAPITestCase):
    
    def test_list_categories(self):
        """Test listing product categories"""
        self.authenticate_user1()
        
        url = reverse('inventory:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)  # At least our 2 test categories


class ReportsAPITest(InventoryAPITestCase):
    
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            user=self.user1,
            name='Report Test Product',
            selling_price=Decimal('100.00'),
            cost_price=Decimal('70.00'),
            category=self.category1
        )
        self.product.inventory.quantity_in_stock = Decimal('50.000')
        self.product.inventory.save()
    
    def test_stock_summary_report(self):
        """Test stock summary report"""
        self.authenticate_user1()
        
        url = reverse('inventory:stock-summary-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        report_data = response.data['data']
        self.assertEqual(len(report_data), 1)
        
        product_data = report_data[0]
        self.assertEqual(product_data['name'], 'Report Test Product')
        self.assertEqual(Decimal(str(product_data['current_stock'])), Decimal('50.000'))
    
    def test_valuation_report(self):
        """Test inventory valuation report"""
        self.authenticate_user1()
        
        url = reverse('inventory:valuation-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        report_data = response.data['data']
        self.assertEqual(len(report_data['products']), 1)
        
        expected_value = Decimal('50.000') * Decimal('70.00')  # stock * cost_price
        self.assertEqual(Decimal(str(report_data['total_inventory_value'])), expected_value)
        self.assertEqual(report_data['currency'], 'ZMW')


class AuthenticationTest(InventoryAPITestCase):
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        url = reverse('inventory:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rate_limiting(self):
        """Test rate limiting on product creation"""
        self.authenticate_user1()
        
        # This test would need to be more sophisticated to actually test rate limiting
        # For now, just verify the endpoint works
        data = {
            'name': 'Rate Limit Test Product',
            'sku': 'RLTP001',
            'selling_price': '50.00',
            'category': self.category1.id
        }
        
        url = reverse('inventory:product-create')
        response = self.client.post(url, data, format='json')
        
        # Should succeed on first request
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
