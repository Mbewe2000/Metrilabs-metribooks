from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Product, ProductCategory, Inventory, StockMovement, StockAlert

User = get_user_model()


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Use get_or_create to avoid unique constraint errors
        self.category, created = ProductCategory.objects.get_or_create(
            name='electronics',
            defaults={'description': 'Electronic products'}
        )
    
    def test_product_creation(self):
        product = Product.objects.create(
            user=self.user,
            name='Test Product',
            sku='TEST001',
            selling_price=Decimal('100.00'),
            cost_price=Decimal('70.00'),
            category=self.category
        )
        
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.sku, 'TEST001')
        self.assertEqual(product.selling_price, Decimal('100.00'))
        self.assertEqual(product.cost_price, Decimal('70.00'))
        # Round the profit margin for comparison
        self.assertAlmostEqual(float(product.profit_margin), 42.86, places=2)
    
    def test_inventory_creation(self):
        product = Product.objects.create(
            user=self.user,
            name='Test Product',
            selling_price=Decimal('100.00')
        )
        
        # Inventory should be created automatically via signals
        self.assertTrue(hasattr(product, 'inventory'))
        self.assertEqual(product.current_stock, 0)


class InventoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            user=self.user,
            name='Test Product',
            selling_price=Decimal('100.00')
        )
        # Get the automatically created inventory and update it
        self.inventory = self.product.inventory
        self.inventory.quantity_in_stock = Decimal('50.000')
        self.inventory.reorder_level = Decimal('10.000')
        self.inventory.save()
    
    def test_stock_status(self):
        # Test in stock
        self.assertEqual(self.inventory.stock_status, 'In Stock')
        self.assertFalse(self.inventory.is_low_stock)
        
        # Test low stock
        self.inventory.quantity_in_stock = Decimal('5.000')
        self.inventory.save()
        self.assertEqual(self.inventory.stock_status, 'Low Stock')
        self.assertTrue(self.inventory.is_low_stock)
        
        # Test out of stock
        self.inventory.quantity_in_stock = Decimal('0.000')
        self.inventory.save()
        self.assertEqual(self.inventory.stock_status, 'Out of Stock')


class StockMovementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            user=self.user,
            name='Test Product',
            selling_price=Decimal('100.00')
        )
    
    def test_stock_movement_creation(self):
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='stock_in',
            quantity=Decimal('10.000'),
            quantity_before=Decimal('0.000'),
            quantity_after=Decimal('10.000'),
            created_by=self.user
        )
        
        self.assertEqual(movement.quantity, Decimal('10.000'))
        self.assertTrue(movement.is_inbound)
        self.assertFalse(movement.is_outbound)
    
    def test_outbound_movement(self):
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='stock_out',
            quantity=Decimal('-5.000'),
            quantity_before=Decimal('10.000'),
            quantity_after=Decimal('5.000'),
            created_by=self.user
        )
        
        self.assertFalse(movement.is_inbound)
        self.assertTrue(movement.is_outbound)


class ProductCategoryModelTest(TestCase):
    def test_category_creation(self):
        # Use get_or_create to avoid unique constraint errors
        category, created = ProductCategory.objects.get_or_create(
            name='electronics',
            defaults={'description': 'Electronic products'}
        )
        
        self.assertEqual(str(category), 'Electronics')
        self.assertTrue(category.is_active)


class StockAlertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            user=self.user,
            name='Alert Test Product',
            selling_price=Decimal('50.00')
        )
    
    def test_stock_alert_creation(self):
        alert = StockAlert.objects.create(
            product=self.product,
            alert_type='low_stock',
            current_stock=Decimal('5.000'),
            reorder_level=Decimal('10.000')
        )
        
        self.assertEqual(alert.product, self.product)
        self.assertEqual(alert.alert_type, 'low_stock')
        self.assertFalse(alert.is_resolved)
        self.assertEqual(str(alert), f"{self.product.name} - Low Stock")
    
    def test_alert_resolution(self):
        alert = StockAlert.objects.create(
            product=self.product,
            alert_type='out_of_stock',
            current_stock=Decimal('0.000')
        )
        
        # Resolve the alert
        alert.is_resolved = True
        alert.save()
        
        self.assertTrue(alert.is_resolved)
