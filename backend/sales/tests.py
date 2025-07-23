from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from sales.models import Sale, SaleItem, SalesReport
from inventory.models import Product, ProductCategory, StockMovement
from services.models import Service, ServiceCategory

User = get_user_model()


class SaleModelTest(TestCase):
    """Test Sale model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_salemodel@example.com',
            password='testpass123'
        )
    
    def test_sale_creation(self):
        """Test creating a basic sale"""
        sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('16.00'),
            discount_amount=Decimal('5.00'),
            total_amount=Decimal('111.00'),
            payment_method='cash',
            status='completed'
        )
        
        self.assertEqual(sale.user, self.user)
        self.assertEqual(sale.subtotal, Decimal('100.00'))
        self.assertEqual(sale.total_amount, Decimal('111.00'))
        self.assertEqual(sale.payment_method, 'cash')
        self.assertTrue(sale.sale_number)  # Should auto-generate
        self.assertIsNotNone(sale.sale_date)
    
    def test_sale_number_generation(self):
        """Test automatic sale number generation"""
        sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            payment_method='cash'
        )
        
        sale2 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('75.00'),
            total_amount=Decimal('75.00'),
            payment_method='mobile_money'
        )
        
        # Both should have sale numbers
        self.assertTrue(sale1.sale_number)
        self.assertTrue(sale2.sale_number)
        
        # Sale numbers should be different
        self.assertNotEqual(sale1.sale_number, sale2.sale_number)
        
        # Should follow pattern SL{YYYYMMDD}{sequence}
        today = datetime.now().strftime('%Y%m%d')
        self.assertTrue(sale1.sale_number.startswith(f'SL{today}'))
        self.assertTrue(sale2.sale_number.startswith(f'SL{today}'))
    
    def test_sale_balance_properties(self):
        """Test balance calculation properties"""
        sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('60.00'),
            payment_method='cash'
        )
        
        self.assertEqual(sale.balance_due, Decimal('40.00'))
        self.assertFalse(sale.is_fully_paid)
        
        # Update payment
        sale.amount_paid = Decimal('100.00')
        sale.save()
        
        self.assertEqual(sale.balance_due, Decimal('0.00'))
        self.assertTrue(sale.is_fully_paid)
    
    def test_sale_user_isolation(self):
        """Test that sales are isolated by user"""
        user2 = User.objects.create_user(
            email='user2_salemodel@example.com',
            password='testpass123'
        )
        
        sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            payment_method='cash'
        )
        
        sale2 = Sale.objects.create(
            user=user2,
            subtotal=Decimal('75.00'),
            total_amount=Decimal('75.00'),
            payment_method='cash'
        )
        
        # Each user should only see their own sales
        user1_sales = Sale.objects.filter(user=self.user)
        user2_sales = Sale.objects.filter(user=user2)
        
        self.assertEqual(user1_sales.count(), 1)
        self.assertEqual(user2_sales.count(), 1)
        self.assertEqual(user1_sales.first(), sale1)
        self.assertEqual(user2_sales.first(), sale2)


class SaleItemModelTest(TestCase):
    """Test SaleItem model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_saleitem@example.com',
            password='testpass123'
        )
        
        self.sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            payment_method='cash'
        )
        
        # Create inventory category and product
        self.category = ProductCategory.objects.create(
            name='electronics_saleitem',
            description='Electronic items'
        )
        
        self.product = Product.objects.create(
            user=self.user,
            name='Laptop SaleItem',
            description='Gaming laptop',
            category=self.category,
            selling_price=Decimal('1500.00'),
            cost_price=Decimal('1200.00')
        )
        
        # Create inventory for the product
        from inventory.models import Inventory
        if not hasattr(self.product, 'inventory'):
            Inventory.objects.create(
                product=self.product,
                quantity_in_stock=Decimal('10.00'),
                reorder_level=Decimal('2.00')
            )
        
        # Create service category and service
        self.service_category = ServiceCategory.objects.create(
            name='IT Services SaleItem',
            description='Technology services'
        )
        
        self.service = Service.objects.create(
            name='Computer Repair',
            description='Computer repair service',
            category=self.service_category,
            pricing_type='fixed',
            fixed_price=Decimal('100.00')
        )
    
    def test_product_sale_item_creation(self):
        """Test creating a sale item for a product"""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name=self.product.name,
            quantity=Decimal('2.000'),
            unit_price=self.product.selling_price,
            total_price=Decimal('3000.00')
        )
        
        self.assertEqual(sale_item.item_type, 'product')
        self.assertEqual(sale_item.product, self.product)
        self.assertEqual(sale_item.quantity, Decimal('2.000'))
        self.assertEqual(sale_item.unit_price, Decimal('1500.00'))
        self.assertEqual(sale_item.total_price, Decimal('3000.00'))
    
    def test_service_sale_item_creation(self):
        """Test creating a sale item for a service"""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            item_type='service',
            service=self.service,
            item_name=self.service.name,
            quantity=Decimal('1.000'),
            unit_price=self.service.fixed_price,
            total_price=self.service.fixed_price
        )
        
        self.assertEqual(sale_item.item_type, 'service')
        self.assertEqual(sale_item.service, self.service)
        self.assertEqual(sale_item.quantity, Decimal('1.000'))
        self.assertEqual(sale_item.unit_price, Decimal('100.00'))
        self.assertEqual(sale_item.total_price, Decimal('100.00'))
    
    def test_sale_item_with_discount(self):
        """Test sale item with discount applied"""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name=self.product.name,
            quantity=Decimal('1.000'),
            unit_price=self.product.selling_price,
            discount_amount=Decimal('100.00'),
            total_price=Decimal('1400.00')  # 1500 - 100 discount
        )
        
        self.assertEqual(sale_item.discount_amount, Decimal('100.00'))
        self.assertEqual(sale_item.total_price, Decimal('1400.00'))


class SalesInventoryIntegrationTest(TestCase):
    """Test sales and inventory integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_inventory@example.com',
            password='testpass123'
        )
        
        self.category = ProductCategory.objects.create(
            name='electronics_inventory',
            description='Electronic items'
        )
        
        self.tracked_product = Product.objects.create(
            user=self.user,
            name='Smartphone Inventory',
            description='Latest smartphone',
            category=self.category,
            selling_price=Decimal('800.00'),
            cost_price=Decimal('600.00')
        )
        
        # Create inventory for tracked product
        from inventory.models import Inventory
        if not hasattr(self.tracked_product, 'inventory'):
            Inventory.objects.create(
                product=self.tracked_product,
                quantity_in_stock=Decimal('20.00'),
                reorder_level=Decimal('5.00')
            )
        
        self.untracked_product = Product.objects.create(
            user=self.user,
            name='Phone Case Inventory',
            description='Protective case',
            category=self.category,
            selling_price=Decimal('25.00'),
            cost_price=Decimal('15.00')
        )
        # No inventory created for untracked product
        
        self.sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            payment_method='cash'
        )
    
    def test_inventory_reduction_on_tracked_product_sale(self):
        """Test that inventory is reduced when selling tracked products"""
        initial_stock = self.tracked_product.current_stock
        
        # Create sale item for tracked product
        SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.tracked_product,
            item_name=self.tracked_product.name,
            quantity=Decimal('3.000'),
            unit_price=self.tracked_product.selling_price,
            total_price=Decimal('2400.00')
        )
        
        # Refresh product from database
        self.tracked_product.refresh_from_db()
        
        # Stock should be reduced
        expected_stock = initial_stock - Decimal('3.000')
        self.assertEqual(self.tracked_product.current_stock, expected_stock)
        
        # Inventory movement should be created
        movement = StockMovement.objects.filter(
            product=self.tracked_product,
            movement_type='sale'
        ).first()
        
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, -Decimal('3.000'))  # Negative for outbound
        self.assertEqual(movement.created_by, self.user)
    
    def test_automatic_inventory_tracking_for_all_products(self):
        """Test that all products automatically get inventory tracking via signals"""
        # Verify that even the 'untracked_product' actually has inventory now due to signals
        from inventory.models import Inventory
        
        # The signal should have created inventory for this product
        self.assertTrue(Inventory.objects.filter(product=self.untracked_product).exists())
        
        # Create sale item for this product
        SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.untracked_product,
            item_name=self.untracked_product.name,
            quantity=Decimal('5.000'),
            unit_price=self.untracked_product.selling_price,
            total_price=Decimal('125.00')
        )
        
        # Stock movement should be created since all products have inventory
        movement = StockMovement.objects.filter(
            product=self.untracked_product
        ).first()
        
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, -5)  # Negative for sales (stock reduction)
        self.assertEqual(movement.movement_type, 'sale')
    
    def test_inventory_restoration_on_sale_item_deletion(self):
        """Test that inventory is restored when sale items are deleted"""
        initial_stock = self.tracked_product.current_stock
        
        # Create sale item
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.tracked_product,
            item_name=self.tracked_product.name,
            quantity=Decimal('2.000'),
            unit_price=self.tracked_product.selling_price,
            total_price=Decimal('1600.00')
        )
        
        # Verify stock was reduced
        self.tracked_product.refresh_from_db()
        self.assertEqual(self.tracked_product.current_stock, initial_stock - Decimal('2.000'))
        
        # Delete the sale item
        sale_item.delete()
        
        # Verify stock was restored
        self.tracked_product.refresh_from_db()
        self.assertEqual(self.tracked_product.current_stock, initial_stock)
        
        # Verify reverse inventory movement was created
        reverse_movement = StockMovement.objects.filter(
            product=self.tracked_product,
            movement_type='return'
        ).first()
        
        self.assertIsNotNone(reverse_movement)
        self.assertEqual(reverse_movement.quantity, Decimal('2.000'))  # Positive for inbound


class SaleSignalsTest(TestCase):
    """Test sale-related signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_signals@example.com',
            password='testpass123'
        )
        
        self.category = ProductCategory.objects.create(
            name='books_stationery_signals',
            description='Books and literature'
        )
        
        self.product = Product.objects.create(
            user=self.user,
            name='Python Book Signals',
            description='Learn Python programming',
            category=self.category,
            selling_price=Decimal('50.00'),
            cost_price=Decimal('30.00')
        )
        
        # Create inventory for the product
        from inventory.models import Inventory
        if not hasattr(self.product, 'inventory'):
            Inventory.objects.create(
                product=self.product,
                quantity_in_stock=Decimal('15.00')
            )
        
        self.sale = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            payment_method='cash'
        )
    
    def test_sale_total_recalculation_on_item_addition(self):
        """Test that sale totals are recalculated when items are added"""
        # Initial sale should have zero totals
        self.assertEqual(self.sale.subtotal, Decimal('0.00'))
        
        # Add first item
        SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name=self.product.name,
            quantity=Decimal('2.000'),
            unit_price=Decimal('50.00'),
            total_price=Decimal('100.00')
        )
        
        # Refresh sale and check totals
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.subtotal, Decimal('100.00'))
        
        # Add second item
        SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name='Another Item',
            quantity=Decimal('1.000'),
            unit_price=Decimal('25.00'),
            total_price=Decimal('25.00')
        )
        
        # Refresh and check updated totals
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.subtotal, Decimal('125.00'))
    
    def test_sale_total_recalculation_on_item_removal(self):
        """Test that sale totals are recalculated when items are removed"""
        # Add items to sale
        item1 = SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name=self.product.name,
            quantity=Decimal('1.000'),
            unit_price=Decimal('50.00'),
            total_price=Decimal('50.00')
        )
        
        item2 = SaleItem.objects.create(
            sale=self.sale,
            item_type='product',
            product=self.product,
            item_name='Another Item',
            quantity=Decimal('1.000'),
            unit_price=Decimal('30.00'),
            total_price=Decimal('30.00')
        )
        
        # Check initial total
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.subtotal, Decimal('80.00'))
        
        # Remove one item
        item1.delete()
        
        # Check updated total
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.subtotal, Decimal('30.00'))


class SalesReportTest(TestCase):
    """Test sales reporting functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_reports@example.com',
            password='testpass123'
        )
        
        # Create some sales for testing
        self.today = timezone.now().date()
        self.yesterday = self.today - timedelta(days=1)
        
        self.sale1 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            payment_method='cash',
            sale_date=timezone.now() - timedelta(days=0)
        )
        
        self.sale2 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            payment_method='mobile_money',
            sale_date=timezone.now() - timedelta(days=1)
        )
        
        self.sale3 = Sale.objects.create(
            user=self.user,
            subtotal=Decimal('150.00'),
            total_amount=Decimal('150.00'),
            payment_method='cash',
            sale_date=timezone.now() - timedelta(days=7)
        )
    
    def test_sales_user_isolation_in_reports(self):
        """Test that reports only include user's own sales"""
        user2 = User.objects.create_user(
            email='user2_reports@example.com',
            password='testpass123'
        )
        
        # Create sale for different user
        Sale.objects.create(
            user=user2,
            subtotal=Decimal('500.00'),
            total_amount=Decimal('500.00'),
            payment_method='cash'
        )
        
        # User 1 should only see their own sales
        user1_sales = Sale.objects.filter(user=self.user)
        self.assertEqual(user1_sales.count(), 3)
        
        # User 2 should only see their sale
        user2_sales = Sale.objects.filter(user=user2)
        self.assertEqual(user2_sales.count(), 1)
    
    def test_sales_date_filtering(self):
        """Test filtering sales by date"""
        today_sales = Sale.objects.filter(
            user=self.user,
            sale_date__date=self.today
        )
        self.assertEqual(today_sales.count(), 1)
        
        yesterday_sales = Sale.objects.filter(
            user=self.user,
            sale_date__date=self.yesterday
        )
        self.assertEqual(yesterday_sales.count(), 1)
    
    def test_sales_payment_method_filtering(self):
        """Test filtering sales by payment method"""
        cash_sales = Sale.objects.filter(
            user=self.user,
            payment_method='cash'
        )
        self.assertEqual(cash_sales.count(), 2)
        
        mobile_money_sales = Sale.objects.filter(
            user=self.user,
            payment_method='mobile_money'
        )
        self.assertEqual(mobile_money_sales.count(), 1)
